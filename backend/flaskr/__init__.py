import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


# pagination
def list_pagination(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        if len(categories) == 0:
            abort(404)

        else:
            categories_array = {}
            for category in categories:
                categories_array[category.id] = category.type

        return jsonify({
            'success': True,
            'categories': categories_array
        })

    @app.route('/questions', methods=['GET'])
    def get_questions():

        all_questions = Question.query.order_by(Question.id).all()
        list_questions = list_pagination(request, all_questions)

        if len(list_questions) == 0:
            abort(404)

        categories = Category.query.order_by(Category.type).all()

        categories_array = {}
        for category in categories:
            categories_array[category.id] = category.type

        return jsonify({
            'success': True,
            'questions': list_questions,
            'total_questions': len(all_questions),
            'categories': categories_array,
            'current_category': None
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):

        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            question.delete()

            all_questions = Question.query.order_by(Question.id).all()
            list_questions = list_pagination(request, all_questions)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    'questions': list_questions,
                    'total_questions': len(all_questions),
                })
        except Exception as e:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        question = body.get('question', None)
        answer = body.get('answer', None)
        difficulty = body.get('difficulty', None)
        category = body.get('category', None)

        if question == "" or answer == "":
            abort(422)

        try:
            create_question = Question(
                question=question,
                answer=answer,
                difficulty=difficulty,
                category=category
            )

            all_questions = Question.query.order_by(Question.id).all()
            list_questions = list_pagination(request, all_questions)

            create_question.insert()

            return jsonify({
                'success': True,
                'created': create_question.id,
                'questions': list_questions,
                'total_questions': len(all_questions)
            })
        except Exception as e:
            abort(422)

    @app.route('/search', methods=['POST'])
    def search_question():

        body = request.get_json()
        search = body.get('searchTerm', None)

        if search:

            questions = Question.query.order_by(Question.id).filter(
                Question.question.ilike('%{}%'.format(search))).all()

            list_questions = list_pagination(request, questions)

            if len(list_questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': list_questions,
                'total_questions': len(questions),
                'current_category': None,
            })
        else:
            abort(404)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):

        all_questions = Question.query.filter(
            Question.category == category_id).order_by(Question.id).all()

        list_questions = list_pagination(request, all_questions)

        if len(list_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': list_questions,
            'total_questions': len(all_questions),
            'current_category': category_id
        })

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():

        body = request.get_json()

        category = body.get('quiz_category', None)
        previous_questions = body.get('previous_questions', None)

        try:

            if category['id'] == 0:
                all_questions = Question.query.filter(
                    Question.id.notin_((previous_questions))).all()
            else:
                all_questions = Question.query.filter_by(
                    category=category['id']).filter(Question.id.notin_(
                        (previous_questions))).all()

            new_id = random.randrange(0, len(all_questions))
            random_question = all_questions[new_id].format()

            return jsonify({
                'success': True,
                'question': random_question
            })
        except Exception as e:
            abort(404)

# ERROR HANDLERS
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(401)
    def not_found_error(error):
        return jsonify({
            "success": False,
            "error": 401,
            "message": "Unauthorized"
        }), 401

    @app.errorhandler(403)
    def not_found_error(error):
        return jsonify({
            "success": False,
            "error": 403,
            "message": "Forbidden"
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(409)
    def not_found_error(error):
        return jsonify({
            "success": False,
            "error": 409,
            "message": "Conflict"
        }), 409

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    return app
