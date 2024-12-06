from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException
from openai import OpenAIError
from agent import LLMAgent
import base64
app = Flask(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    print("Error handler called")
    print(f"Error: {str(e)}")
    
    if isinstance(e, HTTPException):
        return jsonify(error=str(e)), e.code
    
    if isinstance(e, OpenAIError):
        return jsonify(error=str(e)), 401
    
    return jsonify(error="Internal server error"), 500


@app.route('/grade', methods=['POST'])
def grade():
    #preprocess data into array of criterias
    data = request.get_json()
    
    required_fields = ["model", "apikey", "courseid", "language"]
    missing_fields = [field for field in required_fields if field not in data]
    

    if missing_fields:
        return jsonify({
            "error": f"Missing parameter(s): {', '.join(missing_fields)}",
            "missing_fields": missing_fields
        }), 400
        
    print("nem itt van a hiba")

    try:
        llm_agent = LLMAgent(int(data["model"]), data["apikey"], data["language"])
        if llm_agent.model is None:
            raise ValueError("Failed to create LLM agent model.")
    except (OpenAIError, ValueError) as e:
        print("error catched respond with 400")
        abort(401, description=f"{str(e)}")

    print("Calling the evaluation function")
    try:
        assessment = llm_agent.evaluate(
            data["questiontext"], data["courseid"], data["answer"],
            data["criterias"], data["examples"], data['xurl'], data['xresources']
        )
    except OpenAIError as e:
        print("error catched respond with 401")
        abort(401, description=f"Failed to evaluate: {str(e)}")
    except Exception as e:
        print("error catched respond with 500")
        abort(500, description=f"Failed to evaluate: {str(e)}")

    print("Assessment:")
    print(assessment)
    return jsonify(assessment), 200


@app.route('/', methods=['GET'])
def llmagent_test():
    print("root function called")

    data = request.get_json()

    print(data)

    return "ok", 200

@app.route('/generate_question', methods=['POST'])
def generate_question():
    print("generate question")

    data = request.get_json()
    
    required_fields = ["model", "apikey", "courseid", "language"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({
            "error": f"Missing parameter(s): {', '.join(missing_fields)}",
            "missing_fields": missing_fields
        }), 400
        

    try:
        llm_agent = LLMAgent(int(data["model"]), data["apikey"], data["language"])
        if llm_agent.model is None:
            raise ValueError("Failed to create LLM agent model.")
    except (OpenAIError, ValueError) as e:
        print("error catched respond with 400")
        abort(401, description=f"Failed to create LLM client: {str(e)}")

    print("Calling the generate_questions function")
    retval = llm_agent.generate_questions(data["courseid"], data['questions'], data['prompt'], data['xurl'], data['xresources'])
        
    return jsonify(retval)

@app.route('/update_module', methods=['POST'])
def update_module():
    data = request.get_json()
    
    required_fields = ["model", "apikey", "activity", "action", "courseid", "object_id", "language"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({
            "error": f"Missing parameter(s): {', '.join(missing_fields)}",
            "missing_fields": missing_fields
        }), 400
        
    
    try:
        llm_agent = LLMAgent(int(data["model"]), data["apikey"], data["language"])
        if llm_agent.model is None:
            raise ValueError("Failed to create LLM agent model.")
    except (OpenAIError, ValueError) as e:
        print("error catched respond with 400")
        abort(401, description=f"Failed to create LLM client: {str(e)}")
    
    if data['activity'] == "url" and data['action'] != 2:
        required_fields = ["name", "url"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            abort(400, description=f"Missing parameter(s): {', '.join(missing_fields)}")


        mimetype = "url"
        content_name = data["name"]
        decoded_contents = data['url']
        
    if data['activity'] == "resource" and data['action'] != 2:
        required_fields = ["mimetype", "filename", "contents"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            abort(400, description=f"Missing parameter(s): {', '.join(missing_fields)}")

        mimetype = data["mimetype"]
        content_name = data["filename"]
        decoded_contents = base64.b64decode(data["contents"])
    
    
    if data['action'] == 0 or data['action'] == 1:
        #create a document
        try:
            llm_agent.create_or_update_document(data["courseid"], content_name, data["object_id"], decoded_contents, mimetype, data['action'])
        except Exception as e:
            abort(500, description=f"Document creation or update error: {str(e)}")
    else:
        #delete a document
        try:
            llm_agent.delete_document(data["courseid"], data["object_id"])
        except Exception as e:
            abort(500, description=f"Document deletion error: {str(e)}")
        
    return jsonify({
        "state": "success",
    }), 200

