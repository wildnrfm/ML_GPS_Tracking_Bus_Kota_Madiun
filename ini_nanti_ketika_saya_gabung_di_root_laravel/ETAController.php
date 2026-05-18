<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\ETAService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

/**
 * ETAController
 * =============
 * Controller Laravel untuk endpoint ETA yang dipanggil Flutter.
 *
 * Routes (tambahkan di routes/api.php):
 *   Route::post('/eta/predict',         [ETAController::class, 'predict']);
 *   Route::post('/eta/predict/explain', [ETAController::class, 'predictWithExplanation']);
 *   Route::get('/eta/health',           [ETAController::class, 'health']);
 */
class ETAController extends Controller
{
    public function __construct(protected ETAService $etaService) {}

    /**
     * POST /api/eta/predict
     * Prediksi ETA dan kembalikan ke Flutter.
     */
    public function predict(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'start_lat'      => 'required|numeric|between:-90,90',
            'start_lon'      => 'required|numeric|between:-180,180',
            'end_lat'        => 'required|numeric|between:-90,90',
            'end_lon'        => 'required|numeric|between:-180,180',
            'departure_time' => 'nullable|date',
            'distance_km'    => 'nullable|numeric|min:0',
            'bus_id'         => 'nullable|string',
            'route_name'     => 'nullable|string',
            'student_count'  => 'nullable|integer|min:0',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal.',
                'errors'  => $validator->errors(),
            ], 422);
        }

        $result = $this->etaService->predictETA($validator->validated());

        if (!$result['success']) {
            return response()->json([
                'success' => false,
                'message' => $result['message'],
            ], 503);
        }

        return response()->json([
            'success' => true,
            'data'    => $result['data'],
        ]);
    }

    /**
     * POST /api/eta/predict/explain
     * Prediksi ETA + penjelasan Generative AI.
     */
    public function predictWithExplanation(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'start_lat'     => 'required|numeric',
            'start_lon'     => 'required|numeric',
            'end_lat'       => 'required|numeric',
            'end_lon'       => 'required|numeric',
            'departure_time'=> 'nullable|date',
            'distance_km'   => 'nullable|numeric|min:0',
            'bus_id'        => 'nullable|string',
            'route_name'    => 'nullable|string',
            'student_count' => 'nullable|integer|min:0',
        ]);

        if ($validator->fails()) {
            return response()->json(['success' => false, 'errors' => $validator->errors()], 422);
        }

        $result = $this->etaService->predictETAWithExplanation($validator->validated());

        if (!$result['success']) {
            return response()->json(['success' => false, 'message' => $result['message']], 503);
        }

        return response()->json(['success' => true, 'data' => $result['data']]);
    }

    /**
     * GET /api/eta/health
     * Cek apakah ML service aktif.
     */
    public function health(): JsonResponse
    {
        $isHealthy = $this->etaService->isHealthy();

        return response()->json([
            'success'    => $isHealthy,
            'ml_service' => $isHealthy ? 'online' : 'offline',
            'message'    => $isHealthy
                ? 'ML ETA service berjalan normal.'
                : 'ML ETA service tidak dapat dijangkau.',
        ], $isHealthy ? 200 : 503);
    }
}
