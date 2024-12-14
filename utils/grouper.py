from itertools import zip_longest


def xgrouper(iterable, n):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=None)
