"""
This was done to study the material for a scientific work.
The code was tested on the following datasets:
    - 000webhost - https://github.com/danielmiessler/SecLists/blob/master/Passwords/Leaked-Databases/000webhost.txt (~720k)
    - pwlds - https://github.com/Infinitode/PWLDS (~15m)
    - rockyou - https://github.com/Madhava-mng/RockYou.txt (~14m)

All materials were taken from the public domain.
AI participated in writing the code.

To use the program, the data must be in a certain format, for example:
passwords.txt:
    dsfsdfdsf
    32rrrew
    ....
    FDShgg4@@#!!
"""

import os
from collections import Counter

count_base_structures = Counter()   # сount of base structures
count_alpha = {}                    # сount of alphas
count_digits = {}                   # сount of digits
count_other = {}                    # сount of others
count_capitalization = {}           # сount of capitalizations

def is_valid_password(password: str) -> bool:
    """
    Only passwords from printable ASCII (0x20–0x7E).
    """
    if not password:
        return False

    for ch in password:
        code = ord(ch)
        if code < 32 or code > 126:
            return False

    return True


def make_capitalization_mask(alpha_str: str) -> str:
    """
    Builds a mask.
    U = Upper, L = Lower.
    """
    mask = []
    for ch in alpha_str:
        if ch.isupper():
            mask.append('U')
        else:
            mask.append('L')
    return ''.join(mask)


def parse_password(password: str):
    """
    It analyzes one password and updates the global counters.
    """

    # section list
    section_list = [(password, None)]

    # alpha (A)
    index = 0
    while index < len(section_list):

        if section_list[index][1] is None:

            working = section_list[index][0].lower() # for alpha
            is_run = False
            start_pos = -1

            for pos, char in enumerate(working): 

                # skip 
                if char.isalpha():
                    if not is_run:
                        is_run = True
                        start_pos = pos

                # save
                if not char.isalpha() or pos == len(working) - 1:
                    if is_run:

                        if char.isalpha():
                            end_pos = pos
                        else:
                            end_pos = pos - 1


                        alpha_value_original = section_list[index][0][start_pos:end_pos + 1] # alpha 
                        alpha_value_lower = alpha_value_original.lower() # for mask

                        new_sections = []

                        # before Alpha
                        if start_pos != 0:
                            new_sections.append(
                                (section_list[index][0][0:start_pos], None)
                            )

                        # alpha
                        new_sections.append(
                            (alpha_value_lower, "A" + str(len(alpha_value_lower)))
                        )

                        # after Alpha
                        if end_pos != len(section_list[index][0]) - 1:
                            new_sections.append(
                                (section_list[index][0][end_pos + 1:], None)
                            )

                        del section_list[index]
                        section_list[index:index] = new_sections

                        # save mask
                        length = len(alpha_value_original)
                        mask = make_capitalization_mask(alpha_value_original)

                        if length not in count_capitalization:
                            count_capitalization[length] = Counter()
                        count_capitalization[length][mask] += 1

                        break

        index += 1

    # digit (D)
    index = 0
    while index < len(section_list):

        if section_list[index][1] is None:

            working = section_list[index][0]
            is_run = False
            start_pos = -1

            for pos, char in enumerate(working):

                if char.isdigit():
                    if not is_run:
                        is_run = True
                        start_pos = pos

                if not char.isdigit() or pos == len(working) - 1:
                    if is_run:

                        if char.isdigit():
                            end_pos = pos
                        else:
                            end_pos = pos - 1

                        digit_value = working[start_pos:end_pos + 1]

                        new_sections = []

                        if start_pos != 0:
                            new_sections.append(
                                (working[0:start_pos], None)
                            )

                        new_sections.append(
                            (digit_value, "D" + str(len(digit_value)))
                        )

                        if end_pos != len(working) - 1:
                            new_sections.append(
                                (working[end_pos + 1:], None)
                            )

                        del section_list[index]
                        section_list[index:index] = new_sections
                        break

        index += 1

    # other (S)
    index = 0
    while index < len(section_list):

        if section_list[index][1] is None:
            value = section_list[index][0]
            section_list[index] = (value, "S" + str(len(value)))

        index += 1

    # base structure
    base_structure = ""
    for section in section_list:
        base_structure += section[1]

    # updating the count base structure
    count_base_structures[base_structure] += 1

    # Updating value counters
    for value, type_len in section_list:
        length = int(type_len[1:])
        category = type_len[0]

        if category == "A":
            if length not in count_alpha:
                count_alpha[length] = Counter()
            count_alpha[length][value] += 1

        elif category == "D":
            if length not in count_digits:
                count_digits[length] = Counter()
            count_digits[length][value] += 1

        elif category == "S":
            if length not in count_other:
                count_other[length] = Counter()
            count_other[length][value] += 1

    return section_list, base_structure


def normalize_counter(counter: Counter) -> dict:
    total = sum(counter.values())
    if total == 0:
        return {}
    return {value: cnt / total for value, cnt in counter.items()}

def normalize_indexed(counters: dict) -> dict:
    result = {}
    for length, counter in counters.items():
        result[length] = normalize_counter(counter)
    return result


def save_probability_file(filepath: str, prob_dict: dict):
    with open(filepath, "w", encoding="utf-8") as f:
        for value, prob in sorted(prob_dict.items(), key=lambda x: -x[1]):
            f.write(f"{value}\t{prob}\n")

def save_ruleset(output_dir: str = "Rules"):
    os.makedirs(output_dir, exist_ok=True)

    # base structures
    probability_bs = normalize_counter(count_base_structures)
    save_probability_file(
        os.path.join(output_dir, "base_structures.txt"),
        probability_bs
    )

    # alpha
    alpha_dir = os.path.join(output_dir, "Alpha")
    os.makedirs(alpha_dir, exist_ok=True)
    prob_alpha = normalize_indexed(count_alpha)
    for length, probs in prob_alpha.items():
        save_probability_file(
            os.path.join(alpha_dir, f"{length}.txt"),
            probs
        )

    # digits
    digits_dir = os.path.join(output_dir, "Digits")
    os.makedirs(digits_dir, exist_ok=True)
    prob_digits = normalize_indexed(count_digits)
    for length, probs in prob_digits.items():
        save_probability_file(
            os.path.join(digits_dir, f"{length}.txt"),
            probs
        )

    # other
    other_dir = os.path.join(output_dir, "Other")
    os.makedirs(other_dir, exist_ok=True)
    prob_other = normalize_indexed(count_other)
    for length, probs in prob_other.items():
        save_probability_file(
            os.path.join(other_dir, f"{length}.txt"),
            probs
        )

    # capitalization
    cap_dir = os.path.join(output_dir, "Capitalization")
    os.makedirs(cap_dir, exist_ok=True)
    prob_cap = normalize_indexed(count_capitalization)
    for length, probs in prob_cap.items():
        save_probability_file(
            os.path.join(cap_dir, f"{length}.txt"),
            probs
        )

    print(f"Ruleset saved in: {output_dir}/")
    return {
        "base": probability_bs,
        "alpha": prob_alpha,
        "digits": prob_digits,
        "other": prob_other,
        "capitalization": prob_cap,
    }


def load_passwords(path: str) -> list:
    passwords = []
    skipped = 0

    with open(path, "r", encoding="utf-8", errors="replace") as file:
        for line in file:
            if "\ufffd" in line:
                skipped += 1
                continue

            pwd = line.strip()
            if not pwd or not is_valid_password(pwd):
                skipped += 1
                continue

            passwords.append(pwd)

    print(f"[*] Загружено: {len(passwords)}, отброшено: {skipped}")
    return passwords


if __name__ == "__main__":

    passwords = load_passwords("passwords.txt")

    for pwd in passwords:
        sections, bs = parse_password(pwd)
        print(f"{pwd:12} → {bs:12} {sections}")

    print("count_base_structures:", dict(count_base_structures))
    print("count_alpha:", {k: dict(v) for k, v in count_alpha.items()})
    print("count_digits:", {k: dict(v) for k, v in count_digits.items()})
    print("count_other:", {k: dict(v) for k, v in count_other.items()})
    print("count_capitalization:", {k: dict(v) for k, v in count_capitalization.items()})

    ruleset = save_ruleset("Rules")

    print("\n=== Rules/ ===")
    for root, dirs, files in os.walk("Rules"):
        for name in files:
            path = os.path.join(root, name)
            print(f"\n--- {path} ---")
            with open(path, encoding="utf-8") as f:
                print(f.read().rstrip())