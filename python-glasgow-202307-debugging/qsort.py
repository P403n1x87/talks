# buggy version of quicksort
def qsort(lst):
    if len(lst) <= 1:
        return lst

    pivot = lst[0]

    left = [x for x in lst[1:] if x < pivot]
    right = [x for x in lst[1:] if x > pivot]

    return qsort(left) + [pivot] + qsort(right)


# Test
lst = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
print(f"qsort({lst}) = {qsort(lst)}")  # ¯\_(ツ)_/¯
