def singleton(class_):
    instances = {}

    def get_instance(*args, unique_id=None, **kwargs):
        class_id = (class_, unique_id)

        if class_id not in instances:
            instances[class_id] = class_(*args, **kwargs)
        return instances[class_id]

    return get_instance
