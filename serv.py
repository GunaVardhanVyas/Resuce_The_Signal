import socketio
import uvicorn
import numpy as np
from fastapi import FastAPI
from socketio import AsyncServer

sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

CHANNEL_TRUTH = {
    "4": np.array([45, 120, 200, 310]),
    "9": np.array([10, 50, 90, 140, 180, 220, 270, 310, 350])
}

@sio.event
async def phase_update(sid, data):
    phases_deg = np.array(data['phases'])
    n_elements = str(len(phases_deg))
    
    if n_elements in CHANNEL_TRUTH:
        truth_rad = np.radians(CHANNEL_TRUTH[n_elements])
        phases_rad = np.radians(phases_deg)
        
        # Physics
        vectors = np.exp(1j * (phases_rad + truth_rad))
        resultant = np.sum(vectors)
        
        # Normalized Power (0.0 to 1.0)
        norm_power = (np.abs(resultant)**2 / len(truth_rad)**2)
        
        # SNR Calculation
        # We'll assume a max SNR of 20dB for the demo
        snr_db = 10 * np.log10(norm_power + 1e-6) + 20 
        snr_percent = norm_power * 100
        
        await sio.emit('update_display', {
            'snr_db': float(round(snr_db, 2)),
            'snr_percent': float(round(snr_percent, 2)),
            'res_re': float(resultant.real),
            'res_im': float(resultant.imag),
            'is_winner': bool(snr_percent > 90),
            'vecs': [{'re': float(v.real), 'im': float(v.imag)} for v in vectors]
        })

if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=5690)