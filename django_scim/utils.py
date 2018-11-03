import json

def clean_structure_of_passwords(obj):
    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            if 'password' in key.lower():
                new_obj[key] = '*' * len(value) if value else None
            else:
                new_obj[key] = clean_structure_of_passwords(value)

        return new_obj

    elif isinstance(obj, list):
        return [clean_structure_of_passwords(item) for item in obj]

    else:
        return obj


def get_loggable_body(text):
    if not text:
        return text

    try:
        obj = json.loads(text)
    except:
        return text

    obj = clean_structure_of_passwords(obj)

    return json.dumps(obj)
