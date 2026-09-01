"""
- This was done to study the material for a scientific work.
- All materials were taken from the public domain.
- AI participated in writing the code.

To use the program, the data must be in a certain format, for example:
Rules:
    - Alpha:
        - 1.txt
        - ...txt
    - Digits
    - Others
    - Capitalization
    - base_structures.txt
"""
import os
import heapq
import copy

def load_probability_file(filepath: str) -> list:
    """
    Reads a file with value–probability pairs.

    Returns a list of tuples (value, prob) sorted in descending order of probability.
    """
    items = []
    if not os.path.exists(filepath):
        return items

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if "\t" in line:
                value, prob_str = line.split("\t", 1)
            else:
                continue

            value = value.strip()
            prob_str = prob_str.strip()

            try:
                prob = float(prob_str)
            except ValueError:
                continue

            items.append((value, prob))

    items.sort(key=lambda x: -x[1])
    return items

def load_ruleset(rules_dir: str = "Rules") -> dict:
    """
    Loads all the grammar from the Rules/.
    """
    grammar = {}

    # base structures
    grammar["base"] = load_probability_file(
        os.path.join(rules_dir, "base_structures.txt")
    )

    # Alpha
    alpha_dir = os.path.join(rules_dir, "Alpha")
    if os.path.isdir(alpha_dir):
        for filename in os.listdir(alpha_dir):
            if filename.endswith(".txt"):
                length = filename[:-4]
                grammar["A" + length] = load_probability_file(
                    os.path.join(alpha_dir, filename)
                )

    # digits
    digits_dir = os.path.join(rules_dir, "Digits")
    if os.path.isdir(digits_dir):
        for filename in os.listdir(digits_dir):
            if filename.endswith(".txt"):
                length = filename[:-4]
                grammar["D" + length] = load_probability_file(
                    os.path.join(digits_dir, filename)
                )

    # other
    other_dir = os.path.join(rules_dir, "Other")
    if os.path.isdir(other_dir):
        for filename in os.listdir(other_dir):
            if filename.endswith(".txt"):
                length = filename[:-4]
                grammar["S" + length] = load_probability_file(
                    os.path.join(other_dir, filename)
                )

    # capitalization
    cap_dir = os.path.join(rules_dir, "Capitalization")
    if os.path.isdir(cap_dir):
        for filename in os.listdir(cap_dir):
            if filename.endswith(".txt"):
                length = filename[:-4]
                grammar["C" + length] = load_probability_file(
                    os.path.join(cap_dir, filename)
                )
    
    return grammar

def find_prob(pt: list, base_prob: float, grammar: dict) -> float:
    """
    Multiplies base_prob by the probabilities of the selected replacements.
    """
    prob = base_prob
    for pt_type, index in pt:
        if pt_type not in grammar or index >= len(grammar[pt_type]):
            return 0.0
        prob *= grammar[pt_type][index][1]
    return prob

def initialize_base_structures(grammar: dict) -> list:
    """
    From each Base Structure, it extracts the most likely pre-terminal
    """
    pt_list = []

    for base_structure, base_prob in grammar["base"]:
        replacements = []
        i = 0
        while i < len(base_structure):
            category = base_structure[i]
            i += 1
            length_str = ""
            while i < len(base_structure) and base_structure[i].isdigit():
                length_str += base_structure[i]
                i += 1
            replacements.append(category + length_str)

        pt = []
        for repl in replacements:
            pt.append((repl, 0))

            if repl.startswith("A"):
                length = repl[1:]
                cap_key = "C" + length
                pt.append((cap_key, 0))

        pt_item = {
            "base_prob": base_prob,
            "pt": pt,
            "prob": find_prob(pt, base_prob, grammar),
        }
        pt_list.append(pt_item)

    return pt_list

# ============================================================
# This section was taken from lakiw on github: https://github.com/lakiw/pcfg_cracker
# Read https://github.com/lakiw/pcfg_cracker/blob/master/docs/build/latex/pcfgdevelopersguide.pdf (p. 18-24)

def adoption(child_pt: list, base_prob: float,
                     parent_pos: int, parent_prob: float,
                     grammar: dict) -> bool:
    """
    Adoption:
      - The child may have several possible parents.
      - Only the parent with the lowest probability takes the child.
      - If the probabilities are equal, the one with the lower parent_pos.
    """

    for pos, item in enumerate(child_pt):

        # skipping the current parent
        if pos == parent_pos:
            continue

        # there is no previous parent for this position
        if item[1] == 0:
            continue

        # if the index is already 0 — there is no previous parent for this position
        new_parent_pt = copy.copy(child_pt)
        new_parent_pt[pos] = (new_parent_pt[pos][0], new_parent_pt[pos][1] - 1)

        new_parent_prob = find_prob(new_parent_pt, base_prob, grammar)

        # a parent was found with a lower probability => the child is his
        if new_parent_prob < parent_prob:
            return False

        # the probabilities are equal => the one with the lower pos takes the child
        if new_parent_prob == parent_prob:
            if pos < parent_pos:
                return False

    # no one else is suitable => the child is ours.
    return True

def find_children(pt_item: dict, grammar: dict) -> list:
    children = []
    parent_pt = pt_item["pt"]
    parent_prob = pt_item["prob"]
    base_prob = pt_item["base_prob"]

    for pos, (pt_type, index) in enumerate(parent_pt):

        # there are no more replacements for this position
        if pt_type not in grammar or index + 1 >= len(grammar[pt_type]):
            continue

        # create a child: shift the index at position pos by +1
        child_pt = copy.copy(parent_pt)
        child_pt[pos] = (pt_type, index + 1)

        # Adoption Algorithm
        if adoption(child_pt, base_prob, pos, parent_prob, grammar):
            child_item = {
                "pt": child_pt,
                "base_prob": base_prob,
                "prob": find_prob(child_pt, base_prob, grammar),
            }
            children.append(child_item)

    return children

# ============================================================

def apply_mask(word: str, mask: str) -> str:
    """
    Applies the U/L mask to the word
    """

    result = []
    for ch, m in zip(word, mask):
        if m == "U":
            result.append(ch.upper())
        else:
            result.append(ch.lower())
    return "".join(result)

def generate_password(cur_guess: str, pt: list, grammar: dict):
    """
    Recursively substitutes specific strings from replacement tables.
    """
    if not pt:
        print(cur_guess)
        return

    pt_type, index = pt[0]

    if pt_type.startswith("C"):
        return
    
    if pt_type not in grammar or index >= len(grammar[pt_type]):
        return

    value = grammar[pt_type][index][0]

    if pt_type.startswith("A"):
        if len(pt) < 2 or not pt[1][0].startswith("C"):
            # lowercase
            new_guess = cur_guess + value
            generate_password(new_guess, pt[1:], grammar)
            return

        # mask
        cap_type, cap_index = pt[1]
        if cap_type in grammar and cap_index < len(grammar[cap_type]):
            mask = grammar[cap_type][cap_index][0]
        else:
            # everything is in lowercase
            mask = "L" * len(value)

        value = apply_mask(value, mask)
        # skip both Alpha and the mask.
        generate_password(cur_guess + value, pt[2:], grammar)
    else:
        # D or S — just add it
        generate_password(cur_guess + value, pt[1:], grammar)

def generate_guesses(grammar: dict, limit: int = None):
    """
    Generates passwords in descending order of probability.
    limit — the maximum number of passwords (None = no limit).
    """
    pt_list = initialize_base_structures(grammar)

    # min-heap
    p_queue = []
    counter = 0
    for pt_item in pt_list:
        heapq.heappush(p_queue, (-pt_item["prob"], counter, pt_item))
        counter += 1

    generated = 0

    while p_queue:
        _, _, pt_item = heapq.heappop(p_queue)

        # childs
        for child in find_children(pt_item, grammar):
            heapq.heappush(p_queue, (-child["prob"], counter, child))
            counter += 1

        generate_password("", pt_item["pt"], grammar)

        generated += 1
        if limit is not None and generated >= limit:
            break


if __name__ == "__main__":
    limit = None
    grammar = load_ruleset("Rules")

    generate_guesses(grammar, limit)