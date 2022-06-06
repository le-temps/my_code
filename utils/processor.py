
def replace_value_by_value(object, value1, value2):
    if type(object) is dict:
        for key in object:
            object[key] = replace_value_by_value(object[key], value1, value2)
    elif type(object) is list:
        for e in object:
            e = replace_value_by_value(e, value1, value2)
    else:
        if object == value1:
            object = value2
    return object

def replace_value_by_field_name(object, field, value):
    if type(object) is dict:
        for key in object:
            if key == field:
                object[key] = value
            else:
                object[key] = replace_value_by_field_name(object[key], field, value)
    elif type(object) is list:
        for e in object:
            e = replace_value_by_field_name(e, field, value)
    return object

def delete_field_by_field_name(object, field):
    if type(object) is dict:
        if field in object:
            object.pop(field)
        for key in object:
            if type(object[key]) is dict or type(object[key]) is list:
                delete_field_by_field_name(object[key], field)
    elif type(object) is list:
        for e in object:
            if type(e) is dict or type(e) is list:
                delete_field_by_field_name(e, field)
    return object

if __name__ == "__main__":
    a = {"a": 1, "b": "2", "c":{"a": 1, "b": "2", "c":{"a": 1, "b": "2", "c":""}}}
    print(replace_value_by_value(a, "2", None))
    print(replace_value_by_field_name(a, "b", None))
    print(delete_field_by_field_name(a, "b"))