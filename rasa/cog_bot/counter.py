import json
from word2number import w2n

def count_people(file_path, gender=None, bag=None, hat=None, upper_color=None, lower_color=None, roi_1=None, roi_2=None,
    roi1_persistence_time=None, roi2_persistence_time=None, operator_1=None, operator_2=None, negation_upper_color=False,
    negation_lower_color=False, negation_roi_1=False, negation_roi_2=False,negation_gender=False, search = False):
    """
    Count people based on specified criteria in a JSON file.

    Args:
        file_path (str): Path to the JSON file containing people data.
        gender (str, optional): Gender filter.
        bag (str, optional): Bag presence filter.
        hat (str, optional): Hat presence filter.
        upper_color (str, optional): Upper garment color filter.
        lower_color (str, optional): Lower garment color filter.
        roi_1 (str, optional): Region of interest 1 filter.
        roi_2 (str, optional): Region of interest 2 filter.
        roi1_persistence_time (str, optional): ROI 1 persistence time filter (in words).
        roi2_persistence_time (str, optional): ROI 2 persistence time filter (in words).
        operator_1 (str, optional): Comparison operator for ROI 1 persistence time ('greater', 'lower', 'equal').
        operator_2 (str, optional): Comparison operator for ROI 2 persistence time ('greater', 'lower', 'equal').
        negation_upper_color (bool, optional): Negate upper garment color filter.
        negation_lower_color (bool, optional): Negate lower garment color filter.
        negation_roi_1 (bool, optional): Negate ROI 1 filter.
        negation_roi_2 (bool, optional): Negate ROI 2 filter.
        negation_gender (bool, optional): Negate gender filter.
        search (bool, optional): Search mode flag.

    Returns:
        int or dict: Count of people or dictionary with person IDs and their corresponding zones.
    """
    
    count = 0
    people = dict()
    zones = []

    with open(file_path, 'r') as file:
        data = json.load(file)
    
    for person in data['people']:

        if (((gender is None or person.get('gender') == gender) and negation_gender == False) or (person.get('gender') != gender and negation_gender == True )) and \
        (bag is None or ((person.get('bag') == bag))) and \
        (hat is None or ((person.get('hat') == hat))) and \
        (((upper_color is None or person.get('upper_color') == upper_color) and negation_upper_color == False)  or (negation_upper_color == True and person.get('upper_color') != upper_color)) and \
        (((lower_color is None or person.get('lower_color') == lower_color) and negation_lower_color == False)  or (negation_lower_color == True and person.get('lower_color') != lower_color)) and \
        (((roi_1 is None or person.get(roi_1) > 0) and negation_roi_1 == False) or (negation_roi_1 == True and person.get(roi_1) == 0)) and \
        (((roi_2 is None or person.get(roi_2) > 0) and negation_roi_2 == False) or (negation_roi_2 == True and person.get(roi_2) == 0)) and \
        (roi1_persistence_time is None or 
            (operator_1 == "greater" and person.get('roi1_persistence_time') > w2n.word_to_num(roi1_persistence_time)) or \
            (operator_1 == "lower" and person.get('roi1_persistence_time') < w2n.word_to_num(roi1_persistence_time)) or \
            (operator_1 == "equal" and w2n.word_to_num(roi1_persistence_time) == person.get('roi1_persistence_time'))) and \
        (roi2_persistence_time is None or 
            (operator_2 == "greater" and person.get('roi2_persistence_time') > w2n.word_to_num(roi2_persistence_time)) or \
            (operator_2 == "lower" and person.get('roi2_persistence_time') < w2n.word_to_num(roi2_persistence_time)) or \
            (operator_2 == "equal" and w2n.word_to_num(roi2_persistence_time) == person.get('roi2_persistence_time'))):

            zones.clear()

            if search:
                if person.get('roi1_passages') > 0:
                    zones.append('mivia')
                if person.get('roi2_passages') > 0:
                    zones.append('diem')
                if zones is not None:
                    people[person.get('id')] = zones
            else:
                count += 1
    if search:
        return people
    else:
        return count
