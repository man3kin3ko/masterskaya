class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

def cycle_list(list_to_cycle, round=3):
	div = len(list_to_cycle) % round
	if div != 0:
		if len(list_to_cycle) > round:
			return list_to_cycle + list_to_cycle[0:round - div]
	return list_to_cycle

def truncate(line, length):
	return (line[:length] + '...') if len(line) > length else line