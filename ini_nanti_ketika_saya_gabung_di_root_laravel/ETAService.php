<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * ETAService
 * ==========
 * Service Laravel untuk memanggil FastAPI ML-ETA.
 * 
 * Cara pakai di Controller:
 *   $etaService = new ETAService();
 *   $result = $etaService->predictETA([...]);
 */
class ETAService
{
    protected string $baseUrl;
    protected int $timeout;

    public function __construct()
    {
        // URL FastAPI — dari .env, default ke localhost:8001
        $this->baseUrl = env('ML_ETA_URL', 'http://localhost:8001');
        $this->timeout = 10; // detik
    }

    /**
     * Prediksi ETA dari koordinat GPS.
     *
     * @param array $params [
     *   'start_lat'      => float,
     *   'start_lon'      => float,
     *   'end_lat'        => float,
     *   'end_lon'        => float,
     *   'departure_time' => string|null  (ISO8601, opsional)
     *   'distance_km'    => float|null   (opsional)
     *   'bus_id'         => string|null  (opsional)
     *   'route_name'     => string|null  (opsional)
     *   'student_count'  => int|null     (opsional)
     * ]
     * @return array
     */
    public function predictETA(array $params): array
    {
        try {
            $response = Http::timeout($this->timeout)
                ->post("{$this->baseUrl}/predict", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data'    => $response->json(),
                ];
            }

            Log::warning('ML-ETA API error', [
                'status' => $response->status(),
                'body'   => $response->body(),
            ]);

            return [
                'success' => false,
                'message' => 'ML service mengembalikan error: ' . $response->status(),
                'data'    => null,
            ];

        } catch (\Illuminate\Http\Client\ConnectionException $e) {
            Log::error('ML-ETA service tidak dapat dijangkau', ['error' => $e->getMessage()]);
            return [
                'success' => false,
                'message' => 'ML service tidak tersedia. Silakan coba beberapa saat lagi.',
                'data'    => null,
            ];
        }
    }

    /**
     * Prediksi ETA + penjelasan natural (via Generative AI di FastAPI).
     */
    public function predictETAWithExplanation(array $params): array
    {
        try {
            $response = Http::timeout($this->timeout + 5) // GenAI butuh waktu lebih
                ->post("{$this->baseUrl}/predict/explain", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data'    => $response->json(),
                ];
            }

            return [
                'success' => false,
                'message' => 'Gagal mendapatkan penjelasan ETA.',
                'data'    => null,
            ];

        } catch (\Exception $e) {
            Log::error('ML-ETA explain error', ['error' => $e->getMessage()]);
            return [
                'success' => false,
                'message' => 'Terjadi kesalahan pada layanan ML.',
                'data'    => null,
            ];
        }
    }

    /**
     * Cek status ML service.
     */
    public function isHealthy(): bool
    {
        try {
            $response = Http::timeout(3)->get("{$this->baseUrl}/");
            return $response->successful();
        } catch (\Exception) {
            return false;
        }
    }
}
