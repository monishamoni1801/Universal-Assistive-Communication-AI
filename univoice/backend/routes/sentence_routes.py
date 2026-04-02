# routes/sentence_routes.py
from flask import Blueprint, jsonify
import json
import os

sentence_bp = Blueprint('sentence', __name__, url_prefix='/api/sentences')

# Path to sentences.json
SENTENCES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sentences.json')

@sentence_bp.route('/', methods=['GET'])
def get_all_sentences():
    """Get all sentence categories and sentences"""
    try:
        if os.path.exists(SENTENCES_FILE):
            with open(SENTENCES_FILE, 'r', encoding='utf-8') as f:
                sentences = json.load(f)
            return jsonify({
                'success': True,
                'sentences': sentences,
                'categories': list(sentences.keys())
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sentences file not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sentence_bp.route('/<category>', methods=['GET'])
def get_category_sentences(category):
    """Get sentences for a specific category"""
    try:
        if os.path.exists(SENTENCES_FILE):
            with open(SENTENCES_FILE, 'r', encoding='utf-8') as f:
                sentences = json.load(f)
            
            if category in sentences:
                return jsonify({
                    'success': True,
                    'category': category,
                    'sentences': sentences[category]
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Category "{category}" not found'
                }), 404
        else:
            return jsonify({
                'success': False,
                'error': 'Sentences file not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sentence_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all category names"""
    try:
        if os.path.exists(SENTENCES_FILE):
            with open(SENTENCES_FILE, 'r', encoding='utf-8') as f:
                sentences = json.load(f)
            return jsonify({
                'success': True,
                'categories': list(sentences.keys())
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sentences file not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500