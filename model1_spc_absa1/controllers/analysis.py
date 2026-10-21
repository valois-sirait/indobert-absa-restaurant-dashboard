from flask import Blueprint, jsonify
from flask_login import login_required
from services.analysis_service import run_analysis as service_run_analysis

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/run-analysis', methods=['POST'])
@login_required
def run_analysis():
    try:
        result = service_run_analysis()
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except RuntimeError as re:
        # Jika terjadi RuntimeError di dalam InferenceService (misal model gagal diload)
        return jsonify({
            'success': False,
            'failed': 0,
            'total_processed': 0,
            'message': str(re)
        }), 500
    except Exception as e:
        # Tangkap fatal error
        return jsonify({
            'success': False,
            'failed': 0,
            'total_processed': 0,
            'message': f'Terjadi kesalahan internal server: {str(e)}'
        }), 500