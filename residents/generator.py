"""UIN generator based on MOSIP's configurations

For more information, read the documentations:
- https://docs.mosip.io/1.2.0/id-lifecycle-management/supporting-components/commons/id-generator
- https://github.com/mosip/commons/blob/release-1.2.0/kernel/kernel-idgenerator-service/README.md
"""

import secrets
import string

from stdnum import verhoeff


ASCENDING = "0123456789"
DESCENDING = "9876543210"
ADMIN_UID = [

]


def generate_candidate(length : int = 10) -> str :
    """Cryptographically generate a random UID."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def has_repeating_digits(uid : str, max_dist : int = 2) -> bool :
    """Check if UID has repeating digits above the defined maximum distance."""
    count = 1
    for i in range(1, len(uid)):
        if uid[i] == uid[i-1]:
            count += 1
            if count > max_dist:
                return True
        else:
            count = 1
    return False


def has_sequential_pattern(uid : str, sequence_limit : int = 3) -> bool:
    """Check if UID has a consecutive number pattern, given a sequence limit.
    
    If `sequence_limit` is below 2, the sequence limit is 2. \\
    If `sequence_limit` is above the length of the UID, this will always return a false.
    """
    # No consecutive numbers
    if sequence_limit < 3:
        sequence_limit = 2
    
    if sequence_limit > len(uid):
        return False
    
    if sequence_limit == len(uid):
        return uid in ASCENDING or uid in DESCENDING

    for i in range(len(uid) - sequence_limit):
        seq = uid[i:i+sequence_limit]
        if seq in ASCENDING or seq in DESCENDING:
            return True
    return False


def has_repeating_blocks(uid : str, max_blocks : int = 2) -> bool :
    """Check if UID has repeating blocks of number, given a limit."""
    # No repeating numbers
    if max_blocks < 1:
        max_blocks = 1
    
    if max_blocks >= len(uid):
        return True
    
    blocks = [uid[i:i+max_blocks] for i in range(len(uid) - max_blocks)]
    
    block_count = {}
    for index, block in enumerate(blocks):
        if block not in block_count:
            block_count[block] = (1, index)
        
        curr_count, curr_index = block_count[block]
        if index > curr_index + 1:
            block_count[block] =  (curr_count + 1, index)

            if curr_count + 1 >= max_blocks:
                return True
    
    return False


def has_same_ends(uid : str, end_length : int = 5) -> bool :
    """Check if the first and last N digits of a UID is the same."""
    return uid[:end_length] == uid[-end_length:]


def has_same_ends_reversed(uid : str, end_length : int = 5) -> bool :
    """Check if the first and last N digits reversed of a UID is the same."""
    return uid[:end_length] == uid[-end_length:][::-1]


def has_cycle(uid: str) -> bool :
    """Check if UID is a cycle."""
    for i in range(len(uid)):
        cycle = uid[i:] + uid[:i]

        if cycle in ASCENDING or cycle in DESCENDING:
            return True

    return False


def has_same_prefix_repetition(uid : str, prefix_length : int = 2, max_repeat : int = 5) -> bool :
    """Check if the first N digits of the UID is repeated X times."""

    if prefix_length * max_repeat > len(uid):
        return False
    
    if uid[:prefix_length] * max_repeat in uid:
        return True
    
    return False


def has_adjacent_evens(uid : str, max_even : int = 3) -> bool :
    """Check if UID has N adjacent evens."""
    def _is_even(number : str) -> bool :
        return int(number) % 2 == 0
    
    count = 0
    for digit in uid:
        if _is_even(digit):
            count += 1

            if count >= max_even:
                return True
        else:
            count = 0
    
    return False


def is_valid(uid : str, length : int) -> bool :
    """Check if UID passes MOSIP UIN generation filters."""
    # Only integers with length as specified in `length`
    if len(uid) != length:
        return False
    
    # No alphanumeric characters
    try:
        int(uid)
    except ValueError:
        return False

    # No repeating numbers for 2 or more than 2 digits
    if has_repeating_digits(uid, max_dist=2):
        return False
    
    # No sequential number for 3 or more than 3 digits
    if has_sequential_pattern(uid, sequence_limit=3):
        return False
    
    # Should not be generated sequentially
    # enforced with `generate_candidate`
    
    # Should not have repeated block of numbers for 2 or more than 2 digits
    if has_repeating_blocks(uid, max_blocks=2):
        return False

    # The last digit in the number should be reserved for a checksum
    # enforced in `generate_candidate`

    # The number should not contain '0' or '1' as the first digit.
    if uid[0] == '0' or uid[0] == '1':
        return False
    
    # First 5 digits should be different from the last 5 digits (example - 4345643456)
    if has_same_ends(uid, end_length=5):
        return False
    
    # First 5 digits should be different to the last 5 digits reversed (example - 4345665434)
    if has_same_ends_reversed(uid, end_length=5):
        return False
    
    # Should not be a cyclic figure (example - 4567890123, 6543210987)
    # -> same as Rule 4
    if has_cycle(uid):
        return False
    
    # Should be different from the repetition of the first two digits 5 times (example - 3434343434)
    # -> could be enforced with Rules 3 and 6
    if has_same_prefix_repetition(uid, prefix_length=2, max_repeat=5):
        return False
    
    # Should not contain three even adjacent digits (example - 3948613752)
    if has_adjacent_evens(uid, max_even=3):
        return False
    
    # Should not contain admin defined restricted number
    if uid in ADMIN_UID:
        return False

    return True


def generate_uid(id_length : int = 10) -> str :
    """Generate a UIN based on MOSIP's UIN Generation Filters.

    MOSIP UIN Generation Logic:
    1)  Only integers with length as specified in `length`
    2)  No alphanumeric characters
    3)  No repeating numbers for 2 or more than 2 digits
    4)  No sequential number for 3 or more than 3 digits
    5)  Should not be generated sequentially
    6)  Should not have repeated block of numbers for 2 or more than 2 digits
    7)  The last digit in the number should be reserved for a checksum
    8)  The number should not contain '0' or '1' as the first digit.
    9)  First 5 digits should be different from the last 5 digits (example - 4345643456)
    10) First 5 digits should be different to the last 5 digits reversed (example - 4345665434)
    11) Should not be a cyclic figure (example - 4567890123, 6543210987)
    12) Should be different from the repetition of the first two digits 5 times (example - 3434343434)
    13) Should not contain three even adjacent digits (example - 3948613752)
    14) Should not contain admin defined restricted number

    For more information, read the documentations:
    - https://docs.mosip.io/1.2.0/id-lifecycle-management/supporting-components/commons/id-generator
    - https://github.com/mosip/commons/tree/release-1.2.0/kernel/kernel-idgenerator-service
    """
    while True:
        # ID = (length - 1) Random Numbers + 1 Checksum digit
        candidate = generate_candidate(id_length - 1)
        uid = candidate + verhoeff.calc_check_digit(candidate)
        if is_valid(uid, id_length):
            return uid

def generate_id(id_length : int = 8) -> str :
    """Generate a simple ID where the first number should not be a 0."""
    while True:
        _id = generate_candidate(id_length)

        if _id[0] != "0" : 
            return _id
