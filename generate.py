import sys

from crossword import *

from collections import deque

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            self.domains[var] = {word for word in self.domains[var] if len(word) == var.length}


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        overlap = self.crossword.overlaps[x, y]
        if overlap  == None:
            return False
        todelete = []
        for word in self.domains[x]:
            i = overlap[0]
            j = overlap[1]
            matches = {w2 for w2 in self.domains[y] if word[i] == w2[j]}
            if not matches:# matches is empty
                todelete.append(word)
        self.domains[x] = {w for w in self.domains[x] if w not in todelete}
        if not todelete:
            return False
        return True
        

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        q = []
        if arcs is None:
            for v1 in self.domains.keys():
                for v2 in self.domains.keys():
                    if v1 != v2:
                        q.append((v1, v2))
        else:
            for arc in arcs:
                q.append(arc)
        
        while q != None:
            arc = self.dequeue(q)
            if arc is not None:
                x = arc[0]
                y = arc[1]
                if self.revise(x, y):
                    if (len(self.domains[x]) == 0):
                        return False
                    for z in self.crossword.neighbors(x):
                        if z != y:
                            q.append((z, x))
            else:
                break                
        return True

    def dequeue(self, queue):
        if not queue:
            return None
        return queue.pop(0)

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.domains.keys():
            if var not in assignment:
                return False
        return True
# check consistant
    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        #cheking if all values are distinct
        words = list(assignment.values())
        distinct_words = set(words)
        if len(distinct_words) != len(words):
            return False
        # every value is the correct length
        for v in assignment:
            if v.length != len(assignment[v]):
                return False
        # there are no conflicts between neighboring variables.
        for v1 in assignment:
            v1_neighbors = self.crossword.neighbors(v1)
            for v2 in  v1_neighbors:
                if v2 in assignment:
                    overlap = self.crossword.overlaps[v1, v2]
                    if v1 != v2  and assignment[v1][overlap[0]] != assignment[v2][overlap[1]]:
                        return False
        return True
    
    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        result = {word : 0 for word in self.domains[var]}
        for word in self.domains[var]:
            for nighbor in self.crossword.neighbors(var):
                if nighbor not in assignment:
                    (i , j) = self.crossword.overlaps[var, nighbor]
                    for nighbor_word in self.domains[nighbor]:
                        if word[i] != nighbor_word[j]:
                            result[word] += 1

        ordered_values = sorted(self.domains[var], key=lambda word: result[word])
        return ordered_values

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        min_num = 5000
        degree = -1

        for var in self.domains.keys():
            if var not in assignment:
                num_of_neighbors = len(self.crossword.neighbors(var))
                if len(self.domains[var]) == min_num :
                    if num_of_neighbors > degree:
                        returned_var = var
                        degree = num_of_neighbors
                if len(self.domains[var]) < min_num :
                    returned_var = var
                    degree = num_of_neighbors
        return returned_var


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment) :
            return assignment
        variable = self.select_unassigned_variable(assignment)
        orderd_values = self.order_domain_values(variable,assignment)
        for word in orderd_values:
            assignment[variable] = word
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result is not None:
                    return result
            assignment.pop(variable)
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
