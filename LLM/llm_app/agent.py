from langchain_openai import ChatOpenAI
from openai import OpenAIError
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
import json
import getpass
import os
from bs4 import BeautifulSoup
import math
import re
import ast
from enum import Enum
from language_module import LanguageModule
from vectorstore import VectorStore

class LLMType(Enum):
    GPT_4 = 0
    GPT_4o = 1
    GPT_4o_mini = 2
    MISTRAL = 3
    
class Language(Enum):
    HUNGARIAN = 'hu'
    ENGLISH = 'en'
    
EN_MODULE = LanguageModule("en")
HU_MODULE = LanguageModule("hu")

class LLMAgent:
    
    #Static variable
    DB = VectorStore()
    
    def __init__(self, llm_type: int, api_key: str, language: str):
        self.api_key = api_key
        self.llm_type = LLMType(llm_type)
        
        try:
            self.model = self._create_client()
        except Exception as e:
            print(f"Failed to create client: {str(e)}")
            self.model = None
            raise Exception(f"Failed to create client: {str(e)}")
            
        if language == "en":
            self.language_module = EN_MODULE
        elif language == "hu":
            self.language_module = HU_MODULE

        self.generator_parser = JsonOutputParser(pydantic_object=self.language_module.QuestionList)
        self.evaluator_parser = JsonOutputParser(pydantic_object=self.language_module.Evaluation)
        self.atomic_eval_parser = JsonOutputParser(pydantic_object=self.language_module.AtomicEvaluation)
        

    def _create_client(self):
        try:
            if self.llm_type == LLMType.GPT_4:
                model = ChatOpenAI(model="gpt-4", api_key=self.api_key, temperature=0)
                return model
            if self.llm_type == LLMType.GPT_4o:
                model = ChatOpenAI(model="gpt-4o", api_key=self.api_key, temperature=0)
                return model
            if self.llm_type == LLMType.GPT_4o_mini:
                model = ChatOpenAI(model="gpt-4o-mini", api_key=self.api_key, temperature=0)
                return model
            elif self.llm_type == LLMType.MISTRAL:
                model = ChatMistralAI(model="mistral-large-latest", api_key=self.api_key, temperature=0)
                return model
            else:
                raise ValueError("Unsupported LLM type")
        except Exception as e:
            raise Exception(f"Failed to create client: {str(e)}")
            return None
        
    @staticmethod
    def create_or_update_document(course_id, content_name, object_id, contents, mimetype, action):
        LLMAgent.DB.create_or_update_document(course_id, content_name, object_id, contents, mimetype, action)
        
    @staticmethod 
    def delete_document(course_id, object_id):
        print("delete document agent function called")
        LLMAgent.DB.delete_document(course_id, object_id)

    def retrieve_docs(self, courseid, prompt, type_filter):
        if len(type_filter) == 0:
            return None

        try:
            retrieved_docs = LLMAgent.DB.retrieve(courseid, prompt, type_filter)
        except Exception as e:
            print(f"Failed to retrieve documents: {str(e)}")
            raise Exception(f"Failed to retrieve documents: {str(e)}")
        
        if retrieved_docs is None:
            return None
        
        retrieved_docs_escaped = retrieved_docs.replace('{', '{{').replace('}', '}}')
        return retrieved_docs_escaped
    
    def create_type_filter(self, xurl, xresource):
        type_filter = []
        if xurl == '1':
            type_filter.append("url")
        if xresource == '1':
            type_filter.append("resource")
        return type_filter

    def evaluate(self, questiontext, courseid, answer, criterias, examples, xurl, xresource):

        type_filter = self.create_type_filter(xurl, xresource)
        
        context = self.retrieve_docs(courseid, questiontext, type_filter)
        
        print("context:")
        print(context)

        maxscore = 0
        for i in range(1, 5):
            score = criterias.get(f'score{i}', 0)
            maxscore += int(score) if score else 0
        
        soup = BeautifulSoup(answer, 'html.parser')
        text = soup.get_text()
        answer = ' '.join(text.split())
            
        if len(examples) == 0:
            print("evaluate with no examples")
            assessment = self.evaluate_with_no_examples(questiontext, context, answer, criterias, maxscore)
        else:
            print("evaluate with examples")
            assessment = self.evaluate_with_examples(questiontext, context, answer, criterias, examples, maxscore)

        return assessment  

            
    def evaluate_with_examples(self, questiontext, context, answer, criterias, examples, maxscore):                  

        few_shot_examples = []
        for example in examples:
            e = dict(example)

            if (e.get('answer') != ""):
                few_shot_examples.append({
                    "answer": e.get('answer'),
                    "thought1": criterias.get('thought1') if criterias.get('thought1') else "",
                    "score1": criterias.get('score1', "N/A") if criterias.get('score1') else "",
                    "thought2": criterias.get('thought2', "N/A") if criterias.get('thought2') else "",
                    "score2": criterias.get('score2', "N/A") if criterias.get('score2') else "",
                    "thought3": criterias.get('thought3', "N/A") if criterias.get('thought3') else "",
                    "score3": criterias.get('score3', "N/A") if criterias.get('score3') else "",
                    "thought4": criterias.get('thought4', "N/A") if criterias.get('thought4') else "",
                    "score4": criterias.get('score4', "N/A") if criterias.get('score4') else "",
                    "feedback": e.get('feedback', "N/A") if e.get('feedback') else "",
                    "score": e.get('score', "N/A") if e.get('score') else ""
                })

        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=self.language_module.example_scheme_evaluate,
            examples=few_shot_examples,
        )
        
        print("few_shot_prompt:")
        print(
            few_shot_prompt.invoke({"input": "Who was the father of Mary Ball Washington?"}).to_string()
        )

        eval_chat_history = []    
        
        system_prompt = self.language_module.eval_system_prompt(questiontext, context)
        eval_chat_history.append(("system", system_prompt))
        eval_chat_history.append(few_shot_prompt)
        eval_chat_history.append(("human", self.language_module.eval_human_prompt))  # Escape curly braces
        
        print("eval_chat_history:")
        print(eval_chat_history)
        
        final_evaluator_prompt = ChatPromptTemplate.from_messages(eval_chat_history)
        
        chain = final_evaluator_prompt | self.model | self.evaluator_parser

        try:
            print("invoke chain")
            completion = chain.invoke({
                    "answer": answer,
                })
        except OpenAIError as e:
            raise OpenAIError(f"{str(e)}")    
        except Exception as e:
            raise Exception(f"{str(e)}")

        rounded_score = math.ceil(float(completion["score"]))
        fraction = int(rounded_score) / maxscore
        if fraction > 1:
            fraction = 1

        return {
            "feedback": completion["feedback"],
            "fraction": fraction
        }


    def generate_questions(self, courseid, examples, prompt, xurl, xresource):

        type_filter = self.create_type_filter(xurl, xresource)
        
        context = self.retrieve_docs(courseid, prompt, type_filter)
        
        print("context:")
        print(context)

        few_shot_examples = []

        if len(examples) == 0:
            examples = self.language_module.generation_examples

        for example in examples:
            e = dict(example)
            few_shot_examples.append({
                "questiontext": e.get('questiontext', "N/A") if e.get('questiontext') else "",
                "thought1": e.get('thought1', "N/A") if e.get('thought1') else "",
                "score1": e.get('score1', "N/A") if e.get('score1') else "",
                "thought2": e.get('thought2', "N/A") if e.get('thought2') else "",
                "score2": e.get('score2', "N/A") if e.get('score2') else "",
                "thought3": e.get('thought3', "N/A") if e.get('thought3') else "",
                "score3": e.get('score3', "N/A") if e.get('score3') else "",
                "thought4": e.get('thought4', "N/A") if e.get('thought4') else "",
                "score4": e.get('score4', "N/A") if e.get('score4') else ""
            })

        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=self.language_module.example_scheme_generator,
            examples=few_shot_examples,
        )
        
        print("few_shot_prompt:")
        print(
            few_shot_prompt.invoke({"input": "Who was the father of Mary Ball Washington?"}).to_string()
        )
        
        gen_chat_history = []
        
        system_prompt = self.language_module.generate_system_prompt(prompt, context)
    
        # Composing the prompt: first the system prompt, then the few-shot examples, then the human prompt
        gen_chat_history.append(("system", system_prompt))
        gen_chat_history.append(few_shot_prompt)
        gen_chat_history.append(("human", "{{input}}"))  # Escape curly braces
        
        # Creating the final prompt
        final_generator_prompt = ChatPromptTemplate.from_messages(gen_chat_history)
        
        # Creating the chain
        chain = final_generator_prompt | self.model | self.generator_parser

        #invoke the chain
        try:
            completion = chain.invoke({
                "input": self.language_module.generate_human_prompt,
            })
            
            print("completion finished")
        except OpenAIError as e:
            raise OpenAIError(f"{str(e)}")
        except Exception as e:
            raise Exception(f"{str(e)}")
        
        print("completion:")
        print(completion)
        
        # If the completion is a list, return it as is, otherwise wrap it in a list
        if isinstance(completion, list):
            json_array = completion
        else:
            json_array = [completion]

        return json_array
        
        

    def evaluate_with_no_examples(self, questiontext, escaped_context, answer, criterias, maxscore):
        assessments = []
        chat_history = []
        
        system_prompt = self.language_module.atomic_eval_system_prompt(escaped_context)
        chat_history.append(("system", system_prompt))
        chat_history.append(("human", self.language_module.eval_atomic_human_prompt))  # Escape curly braces
        
        final_eval_prompt = ChatPromptTemplate.from_messages(chat_history)
        
        print("final_eval_prompt:")
        print(final_eval_prompt)
        
        chain = final_eval_prompt | self.model | self.atomic_eval_parser
        
        for i in range(1, 5):
            thought = criterias.get(f'thought{i}')
            if thought is not None:
                assessments.append(self.evaluate_single_criteria(questiontext, answer, thought, criterias.get(f'score{i}'), chain))
            elif i == 1:
                raise Exception("There is no first criteria to evaluate")           
                
        (score, feedbacksummary) = self.summarise(assessments, maxscore, answer)
                
        return {
            "fraction": score,
            "feedback": feedbacksummary
        }
        
    def evaluate_single_criteria(self, questiontext, answer, criteria, score, chain):
            
        try:    
            completion = chain.invoke({
                    "answer": answer,
                    "criteria": criteria,
                    "questiontext": questiontext,
                })
        except OpenAIError as e:
            raise OpenAIError(f"{str(e)}")
        except Exception as e:
            raise Exception(f"{str(e)}")
        
        print("completion:")
        print(completion)
        
        return {
            "points": score,
            "score": completion["score"],
            "feedback": completion["argument"]
        }
        
    
    def summarise(self, assessments, maxscore, answer):
        finalscore = 0
        feedbacks = ""
        
        for assessment in assessments:
            feedbacks += str(assessment.get('feedback')) + "\n"
            if assessment.get('score') == "True":
                print("points:")
                print(assessment.get('points'))
                finalscore += int(assessment.get('points'))
                
        chat_history=[]
        chat_history.append(("system", self.language_module.summarise_eval_system_prompt))
        chat_history.append(("human", self.language_module.summaries_human_prompt))  
        final_eval_prompt = ChatPromptTemplate.from_messages(chat_history)
                
        chain = final_eval_prompt | self.model 
        
        try:    
            completion = chain.invoke({
                    "answer": answer,
                    "reasonings": feedbacks
                })
        except OpenAIError as e:
            raise OpenAIError(f"{str(e)}")
        except Exception as e:
            raise Exception(f"{str(e)}")
        
        rounded_score = math.ceil(float(finalscore))
        fraction = int(rounded_score) / maxscore
        if fraction > 1:
            fraction = 1
        
        return (fraction, str(completion.content))
        
        




