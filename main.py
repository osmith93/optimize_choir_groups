from mip import Model, xsum, maximize, BINARY
import math
FIRST_NAME = 0
LAST_NAME = 1
VOICE = 2
FRIENDS = 5
GROUP_COUNT = 5
VOICE_COUNT = 4
MAX_GROUP_SIZE = 13
MIN_VOICE_SIZE = 2
MAX_VOICE_SIZE = 4


class Person:
    def __init__(self, name):
        self.voice = ''
        split_name = name.split(sep=' ')
        self.first_name = split_name[0]
        self.last_name = split_name[1]

    def __init__(self, first_name, last_name):
        self.voice = ''
        self.first_name = first_name
        self.last_name = last_name

    def set_voice(self, voice):
        self.voice = voice

    def __repr__(self):
        return f"Person('{self.first_name}','{self.last_name}')"

    def __eq__(self, name):
        split_name = name.split(sep=' ')
        if len(split_name) == 1:
            return split_name[0] == self.first_name
        if len(split_name) == 2:
            return (split_name[0] == self.first_name) and (split_name[1] == self.last_name)



# importing data
import csv
data_file_name = './data.csv'
data = []
with open(data_file_name) as file:
    reader = csv.reader(file)
    for row in reader:
        data.append(row)
print(data[0])

# loading all participants
people = []
for row in data[1:]:
    people.append(Person(row[FIRST_NAME].strip(), row[LAST_NAME].strip()))
    people[-1].set_voice(row[VOICE])
print(f'Loaded names of {len(people)} people.')

# checking for friends that were not found
for row in data[1:]:
    friend_list = row[FRIENDS].split(sep=',')
    for friend in friend_list:
        found = False
        friend = friend.strip()
        if friend != '':
            for person in people:
                if person == friend:
                    if found:
                        print(f'{friend} friend of {row[FIRST_NAME]} was found twice!')
                    found = True
            if not found:
                print(f'{friend}, friend of {row[FIRST_NAME]} was not found')

# get ids of people in households
households = []
person_id_of = {}
for p, person in enumerate(people):
    for household in households:
        for other_name in household:
            if person == other_name:
                person_id_of[other_name] = p

# setting up the ILP
L = [] # L[i][j] == 1 <=> person i wants to be in the group of person j
V = [] # V[i][v] == 1 <=> person i is in voice v
for row in data[1:]:
    friends = len(people) * [0]
    friend_list = row[FRIENDS].split(sep=',')
    for friend in friend_list:
        friend = friend.strip()
        if friend != '':
            for friend_id, person in enumerate(people):
                if person == friend:
                    friends[friend_id] = 1
    L.append(friends)
    if row[VOICE] == "Sopran":
        V.append([1, 0, 0, 0])
    if row[VOICE] == "Alt":
        V.append([0, 1, 0, 0])
    if row[VOICE] == "Tenor":
        V.append([0, 0, 1, 0])
    if row[VOICE] == "Bass":
        V.append([0, 0, 0, 1])

Groups = set(range(GROUP_COUNT))
People = set(range(len(people)))
Voices = set(range(4))

model = Model("Optimizing Choir Groups")
X = [[model.add_var(var_type=BINARY) for g in Groups] for p in People]
A = [[[model.add_var(var_type=BINARY) for g in Groups] for p1 in People] for p2 in People]

# objective function
# scaling wishes with 1/sqrt(#wishes)
#model.objective = maximize(xsum(L[p1][p2] * A[p1][p2][g]/math.sqrt(sum(L[p1])+1) for p1 in People for p2 in People for g in Groups))
# scaling wishes with 1/(#wishes)
model.objective = maximize(xsum(L[p1][p2] * A[p1][p2][g]/max(sum(L[p1]),1) for p1 in People for p2 in People for g in Groups))
# scaling wishes with 1
#model.objective = maximize(xsum(L[p1][p2] * A[p1][p2][g] for p1 in People for p2 in People for g in Groups))

# constraint defining A[p1][p2][g] = X[p1][g]*X[p2][g]
for p1 in People:
    for p2 in People:
        for g in Groups:
            model += A[p1][p2][g] <= X[p1][g]
            model += A[p1][p2][g] <= X[p2][g]

# constraints on group size
for g in Groups:
    model += xsum(X[p][g] for p in People) <= MAX_GROUP_SIZE

# everyone is in exactly one group
for p in People:
    model += xsum(X[p][g] for g in Groups) == 1

# assure everyone has at least one wish granted
for p in People:
    if sum(L[p]) > 0:
        model += xsum(L[p][p1] * A[p][p1][g] for p1 in People for g in Groups) >= 1

# set minimum voice size per group
for g in Groups:
    for v in Voices:
        model += xsum(V[p][v] * X[p][g] for p in People) >= MIN_VOICE_SIZE
        model += xsum(V[p][v] * X[p][g] for p in People) <= MAX_VOICE_SIZE

# force households into the same groups
for household in households:
    first_name = household[0]
    for other_name in household[1:]:
        model += xsum(A[person_id_of[first_name]][person_id_of[other_name]][g] for g in Groups) == 1

# optimizing
model.optimize(max_seconds=5)

if model.num_solutions:
    print('Solution was found!')
    for g in Groups:
        voices = {"Alt": 0, "Sopran": 0, "Tenor": 0, "Bass": 0}
        print(f"Group Number {g}:")
        for p in People:
            if X[p][g].x >= 0.99:
                print(f"{people[p].first_name} {people[p].last_name}, {people[p].voice}")
                v = people[p].voice.strip()
                voices[v] += 1
        print(voices)
        print("")

