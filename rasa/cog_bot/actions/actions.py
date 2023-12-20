from typing import Any, Text, Dict, List

from rasa_sdk.events import SlotSet,AllSlotsReset
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import os
import re
import counter
import openai

class ActionOpenAIAnswer(Action):
    """
    Action to generate answers using OpenAI's GPT-3.5-turbo model.

    This action takes the user's input, sends it to the OpenAI API, and receives a response.

    Attributes:
        api_key (str): OpenAI API key.

    """
    def name(self) -> Text:
        return "action_openai_answer"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Execute the action.

        Args:
            dispatcher (CollectingDispatcher): Rasa dispatcher to send messages.
            tracker (Tracker): Rasa conversation tracker.
            domain (Dict[Text, Any]): Rasa domain.

        Returns:
            List[Dict[Text, Any]]: List of events.

        """
        try:

            request = tracker.latest_message.get("text")
            user_interactions = [{"role": "user", "content": request}]

            openai.api_key = os.getenv("OPEN_API_KEY")

            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=user_interactions,
                max_tokens=250
            )

            response = text=completion.choices[0].message.content
            user_interactions.append({"role": "assistant", "content": response})

            while len(user_interactions) >= 3:
                user_interactions.pop(1)

        except Exception as e:
            response = None

        if response is not None:
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text="Sorry, I can't handle this question yet. Try with something else")

        return []

class ActionCountPeople(Action):
    """
    Action to count people based on specified criteria.

    This action reads a JSON file containing people data and applies filters to count the matching individuals.

    Attributes:
        None

    """
    def name(self) -> Text:
        return "action_count"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        file_path = os.path.join(os.path.dirname(__file__), "input_example.json")
        """
        Execute the action.

        Args:
            dispatcher (CollectingDispatcher): Rasa dispatcher to send messages.
            tracker (Tracker): Rasa conversation tracker.
            domain (Dict[Text, Any]): Rasa domain.

        Returns:
            List[Dict[Text, Any]]: List of events.

        """
        # Negation variables
        negation_roi_1 = False  
        negation_roi_2 = False   
        negation_gender = False      
        negation_upper_color = False    
        negation_lower_color = False

        flag_neg = False # flag used to identify the entity to negate in a sentence
 
        # Color variables
        upper_color = None
        lower_color = None

        # Roi time managment
        roi1_persistence_time = None
        roi2_persistence_time = None
        operator_1 = None
        operator_2 = None

        # Values from slots
        gender = tracker.get_slot("gender")
        bag = tracker.get_slot("bag")
        hat = tracker.get_slot("hat")
        roi_1 = tracker.get_slot("roi_1")
        roi_2 = tracker.get_slot("roi_2")
        hat = bool(hat) if hat is not None else None
        bag = bool(bag) if bag is not None else None


        entities = tracker.latest_message.get('entities', [])

        # Color managment

        # List that will contain the color in in the sentence
        colors_list = list(tracker.get_latest_entity_values('color'))
        
        # List that will contain the clothes in order of appearance in the sentence
        clothes_list = list()

        # List that will contain the ROIs in order of appearance in the sentence
        roi_list = list()

        # List that will contain the operators to evaluate the permanence in the ROIs in order of appearance in the sentence
        operators_list = list()

        # List containing all the values in minutes for the time of stay in the ROIs
        time_list = list(tracker.get_latest_entity_values('time'))


        # Iterate over entities to fill the necessary lists 
        for entity in entities:
            e = entity.get("entity")
            if e in ['upper_clothes', 'lower_clothes'] and entity.get('value') is not None:
                clothes_list.append(entity.get('value'))
            elif e in ['roi_1', 'roi_2'] and entity.get('value') is not None:
                roi_list.append(entity.get('value'))
            elif e in ['greater', 'lower','equal'] and entity.get('value') is not None:
                operators_list.append(entity.get('value'))

        # Fill the color lists
        if(len(clothes_list) == 2 and len(colors_list) == 1):
            upper_color = colors_list[0]
            lower_color = colors_list[0]
        elif (len(colors_list) > len(clothes_list)):
            for entity in entities:
                e = entity.get("entity")
                if e == 'color':
                    color = entity.get('value')
                if e == 'upper_clothes':
                    upper_color = color
                elif e == 'lower_clothes':
                    lower_color = color
        else:
            for clothe, color in zip(clothes_list,colors_list):
                if clothe == "upper_clothes":
                    upper_color = color
                elif clothe == "lower_clothes":
                    lower_color = color

        # Fill the ROI lists
        if(len(roi_list)==2 and len(time_list)==1 and len(operators_list)==1):
            roi1_persistence_time = time_list[0]
            roi2_persistence_time = time_list[0]
            operator_1 = operators_list[0]
            operator_2 = operators_list[0]
        elif (len(roi_list) > 0 and len(time_list) > 0 and len(operators_list)==0):
            operator_1 = "equal"
            operator_2 = "equal"
            if(len(roi_list)==2 and len(time_list)==1):
                roi1_persistence_time = time_list[0]
                roi2_persistence_time = time_list[0]
            else:
                for roi, time in zip(roi_list,time_list):
                    if roi == "roi1_passages":
                        roi1_persistence_time = time
                    elif roi == "roi2_passages":
                        roi2_persistence_time = time
        else:
            for roi, time,operator in zip(roi_list,time_list,operators_list):
                if roi == "roi1_passages":
                    roi1_persistence_time = time
                    operator_1 = operator
                elif roi == "roi2_passages":
                    roi2_persistence_time = time
                    operator_2 = operator



        # print("Gender:", gender)
        # print("Bag:", bag)
        # print("Hat:", hat)
        # print("ROI_1:", roi_1)
        # print("ROI_2:", roi_2)
        # print("UPPER",upper_color)
        # print("LOWER",lower_color)
        # print("ROI_1 TIME:", roi1_persistence_time)
        # print("ROI_2 TIME:", roi2_persistence_time)
        # print("ROI_1 OPERATOR:", operator_1)
        # print("ROI_2 OPERATOR:", operator_2)


  
        for entity in entities:
            e = entity.get("entity")
            if e == 'negation':
                flag_neg = True
            if flag_neg:
                if e == 'hat':
                    hat = False
                    flag_neg = False
                elif e == 'bag':
                    bag = False
                    flag_neg = False
                elif e == 'roi_1':
                    negation_roi_1 = True
                    flag_neg = False
                elif e == 'roi_2':
                    negation_roi_2 = True
                    flag_neg = False
                elif e == 'gender':
                    negation_gender = True
                    flag_neg = False
                elif e == 'upper_clothes':
                    negation_upper_color = True
                    flag_neg = False
                elif e == 'lower_clothes':
                    negation_lower_color = True
                    flag_neg = False

        # print("Bag:", bag)
        # print("Hat:", hat)
        # print("NEGAZIONI")
        # print("negation_roi_1:", negation_roi_1)
        # print("negation_roi_2:", negation_roi_2)
        # print("negation_gender:", negation_gender)
        # print("negation_upper_color:", negation_upper_color)
        # print("negation_lower_color:", negation_lower_color)

        try:
            count=counter.count_people(file_path,gender,bag,hat,upper_color,lower_color,roi_1,roi_2,roi1_persistence_time,roi2_persistence_time,operator_1,operator_2, negation_upper_color, negation_lower_color, negation_roi_1, negation_roi_2,negation_gender)
            
            if count == 0:
                output = "There's no one who matches the features you said"
            elif count == 1:
                output = f"There's {count} person who matches these features"
            elif count > 1:
                output = f"There are {count} people who match these features"
            dispatcher.utter_message(text=output)  

        except:
            dispatcher.utter_message("Sorry i didn't understend your question, can you repeate please")

        return [AllSlotsReset()]


class ActionMappingColorInForm(Action):
    """
    Action to map color entities to Rasa slots.

    This action maps color entities to the corresponding slots in the Rasa conversation.

    Attributes:
        None

    """
    def name(self) -> Text:
        return "action_map_color_form"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if str(tracker.latest_message['intent']['name']) == "research_stop":
            return []

        # Color settings   
        upper_color = tracker.get_slot("upper_color")
        lower_color = tracker.get_slot("lower_color")

        entities = tracker.latest_message.get('entities', [])
        clothes_list = [entity.get('value') for entity in entities if entity['entity'] in ['upper_clothes', 'lower_clothes'] and entity.get('value') is not None]
        colors_list = list(tracker.get_latest_entity_values('color'))

        if(len(clothes_list) == 2 and len(colors_list) == 1):
            upper_color = colors_list[0]
            lower_color = colors_list[0]
        elif (len(colors_list) > len(clothes_list)):
            for entity in entities:
                e = entity.get("entity")
                if e == 'color':
                    color = entity.get('value')
                if e == 'upper_clothes':
                    upper_color = color
                elif e == 'lower_clothes':
                    lower_color = color
        else:
            for clothe, color in zip(clothes_list,colors_list):
                if clothe == "upper_clothes":
                    upper_color = color
                elif clothe == "lower_clothes":
                    lower_color = color

        for clothe, color in zip(clothes_list,colors_list):
            if clothe == "upper_clothes":
                upper_color = color
            elif clothe == "lower_clothes":
                lower_color = color

        if upper_color is not None or lower_color is not None:
            return [SlotSet("upper_color", upper_color), SlotSet("lower_color", lower_color)]
        return

class ActionSearchPerson(Action):
    """
    ActionSearchPerson: Rasa action for searching people based on specified features.

    Attributes:
        None
    """
    def name(self) -> Text:
        return "action_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Runs the action to search for people based on specified features.

        Args:
            dispatcher (CollectingDispatcher): The dispatcher object for sending messages.
            tracker (Tracker): The current conversation tracker.
            domain (Dict[Text, Any]): The domain configuration.

        Returns:
            List[Dict[Text, Any]]: A list containing a dictionary with slot resets.
        """
        file_path = os.path.join(os.path.dirname(__file__), "input_example.json")

        gender = str(tracker.get_slot("gender")).lower()
        bag = tracker.get_slot("bag")

        if bag == 'unknown':
            bag = None
        else:
            bag = bool(tracker.get_slot("bag")) if tracker.get_slot("bag") is not None  else None
        
        hat = tracker.get_slot("hat")
        if hat == 'unknown':
            hat = None
        else:
            hat = bool(tracker.get_slot("hat")) if tracker.get_slot("hat") is not None else None
            
        upper_color = str(tracker.get_slot("upper_color")).lower()
        lower_color = str(tracker.get_slot("lower_color")).lower()
            
        if upper_color == 'unknown':
            upper_color = None
        if lower_color == 'unknown':
            lower_color = None               

        people = counter.count_people(file_path, gender, bag, hat,upper_color,lower_color, search=True)
        output = ""

        if len(people) == 0:
            output += "I'm sorry, I didn't find anyone with these features"
        else:
            for key in people.keys():
                output += "\nThere's a person in: "
                for v in people[key]:
                    output += v.upper() + " "

        
        dispatcher.utter_message(text=output)
        return [AllSlotsReset()]

