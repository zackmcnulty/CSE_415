''' zmcnulty_AStar.py
 A* search through problem space.
 Version 0.2, January 23, 2019.
 Zachary McNulty, Univ. of Washington.

 Usage:
 python3 zmcnulty_AStar.py FranceWithCosts

This is a modified version of UCS.py

This implementation does not reconsider a state once it has
been put on CLOSED list.  If this implementation is extended
to implement A*, and it is to work with all heuristics,
including non-admissible ones, then when a state is regenerated
that was already put on the CLOSED list, it may need reconsideration
if the new priority value is lower than the old one.

Most of the print statements have been commented out, but can be
useful for a closer look at execution, or if preparing some
debugging infrastructure before adding extensions, such as for A*.
'''

VERBOSE = False  # Set to True to see progress; but it slows the search.

import sys
import time

if sys.argv==[''] or len(sys.argv)<2:
  import EightPuzzle as Problem
else:
  import importlib
  Problem = importlib.import_module(sys.argv[1])

# Heuristic related to the given problem
h = Problem.h

print("\nWelcome to A* Search!")

COUNT = None # Number of nodes expanded.
MAX_OPEN_LENGTH = None # How long OPEN ever gets.
SOLUTION_PATH = None # List of states from initial to goal, along lowest-cost path.
TOTAL_COST = None # Sum of edge costs along the lowest-cost path.
BACKLINKS = {} # Predecessor links, used to recover the path.

# The value g(s) represents the cost along the best path found so far
# from the initial state to state s.
# this should NOT include our heuristic
# ONLY OUR PRIORITIES (in priority queue) should include heuristic
g = {} # We will use a global hash table to associate g values with states.

class My_Priority_Queue:
  def __init__(self):
    self.q = [] # Actual data goes in a list.

  def __contains__(self, elt):
    '''If there is a (state, priority) pair on the list
    where state==elt, then return True.'''
    #print("In My_Priority_Queue.__contains__: elt= ", str(elt))
    for pair in self.q:
      if pair[0]==elt: return True
    return False

  def delete_min(self):
    ''' Standard priority-queue dequeuing method.'''
    if self.q==[]: return [] # Simpler than raising an exception.
    temp_min_pair = self.q[0]
    temp_min_value = temp_min_pair[1]
    temp_min_position = 0
    for j in range(1, len(self.q)):
      if self.q[j][1] < temp_min_value:
        temp_min_pair = self.q[j]
        temp_min_value = temp_min_pair[1]  
        temp_min_position = j
    del self.q[temp_min_position]
    return temp_min_pair

  def insert(self, state, priority):
    '''We do not keep the list sorted, in this implementation.'''
    #print("calling insert with state, priority: ", state, priority)

    if self[state] != -1:
      print("Error: You're trying to insert an element into a My_Priority_Queue instance,")
      print(" but there is already such an element in the queue.")
      return
    self.q.append((state, priority))

  def __len__(self):
    '''We define length of the priority queue to be the
    length of its list.'''
    return len(self.q)

  def __getitem__(self, state):
    '''This method enables Pythons right-bracket syntax.
    Here, something like  priority_val = my_queue[state]
    becomes possible. Note that the syntax is actually used
    in the insert method above:  self[state] != -1  '''
    for (S,P) in self.q:
      if S==state: return P
    return -1  # This value means not found.

  def __delitem__(self, state):
    '''This method enables Python's del operator to delete
    items from the queue.'''
    #print("In MyPriorityQueue.__delitem__: state is: ", str(state))
    for count, (S,P) in enumerate(self.q):
      if S==state:
        del self.q[count]
        return

  def __str__(self):
    txt = "My_Priority_Queue: ["
    for (s,p) in self.q: txt += '('+str(s)+','+str(p)+') '
    txt += ']'
    return txt

def runAstar():
  '''This is an encapsulation of some setup before running
  Astar, plus running it and then printing some stats.'''
  initial_state = Problem.CREATE_INITIAL_STATE()
  print("Initial State:")
  print(initial_state)
  global COUNT, BACKLINKS, MAX_OPEN_LENGTH, SOLUTION_PATH
  COUNT = 0
  BACKLINKS = {}
  MAX_OPEN_LENGTH = 0

  start_time = time.time()

  SOLUTION_PATH = Astar(initial_state)
  print(str(COUNT)+" states expanded.")
  print('MAX_OPEN_LENGTH = '+str(MAX_OPEN_LENGTH))
  print("runtime (seconds): ", time.time() - start_time)
  #print("The CLOSED list is: ", ''.join([str(s)+' ' for s in CLOSED]))

def Astar(initial_state):
  '''Uniform Cost Search. This is the actual algorithm.'''
  global g, COUNT, BACKLINKS, MAX_OPEN_LENGTH, CLOSED, TOTAL_COST
  CLOSED = []
  BACKLINKS[initial_state] = None
  # The "Step" comments below help relate UCS's implementation to
  # those of Depth-First Search and Breadth-First Search.

# STEP 1a. Put the start state on a priority queue called OPEN
  OPEN = My_Priority_Queue()
  hi = h(initial_state)

  # OPEN stores priorities which take into account our heuristic
  OPEN.insert(initial_state, hi) 

# STEP 1b. Assign g=0 to the start state. g does not count
# our heuristic, but rather the minimum distance to that state
# so far calculated.
  g[initial_state]=0

# STEP 2. If OPEN is empty, output “DONE” and stop.
  while len(OPEN)>0:
    if VERBOSE: report(OPEN, CLOSED, COUNT)
    if len(OPEN)>MAX_OPEN_LENGTH: MAX_OPEN_LENGTH = len(OPEN)

# STEP 3. Select the state on OPEN having lowest priority value and call it S.
#         Delete S from OPEN.
#         Put S on CLOSED.
#         If S is a goal state, output its description
    (S,P) = OPEN.delete_min()
    #print("In Step 3, returned from OPEN.delete_min with results (S,P)= ", (str(S), P))
    CLOSED.append(S)

    if Problem.GOAL_TEST(S):
      print(Problem.GOAL_MESSAGE_FUNCTION(S))
      path = backtrace(S)
      print('Length of solution path found: '+str(len(path)-1)+' edges')
      TOTAL_COST = g[S]
      print('Total cost of solution path found: '+str(TOTAL_COST))
      return path
    COUNT += 1

# STEP 4. Generate each successors of S and delete 
#         and if it is already on CLOSED, delete the new instance.
    gs = g[S] # Save the cost of getting to S in a variable.
    for op in Problem.OPERATORS:
      if op.precond(S):
        new_state = op.state_transf(S)
        # calculate the heuristic for the new state
        hs = h(new_state)
        edge_cost = S.edge_distance(new_state)

        # calculate the new true distance
        new_g = gs + edge_cost
        new_f = new_g + hs

        if (new_state in CLOSED):
          #print("Already have this state, in CLOSED. del ...")


          # we have already added this state to closed, but we found a shorter path
          # to it. This implies we must re-expand it.

          # equivalent to asking new_g < g[new_state]
          if new_f < g[new_state] + hs:
              g[new_state] = new_g
              CLOSED.remove(new_state)
              OPEN.insert(new_state,  new_f)
              BACKLINKS[new_state] = S
          else:
              del new_state
          continue

        # If new_state already exists on OPEN:
        #   If its new priority is less than its old priority,
        #     update its priority on OPEN, and set its BACKLINK to S.
        #   Else: forget out this new state object... delete it.

        if new_state in OPEN:
          #print("new_state is in OPEN already, so...")
          P = OPEN[new_state]
          if new_f < P:
            #print("New priority value is lower, so del older one")
            del OPEN[new_state]
            OPEN.insert(new_state, new_f)
          else:
            #print("Older one is better, so del new_state")
            del new_state
            continue
        else:
            #print("new_state was not on OPEN at all, so just put it on.")
            OPEN.insert(new_state, new_f)
        BACKLINKS[new_state] = S
        g[new_state] = new_g

    #print_state_queue("OPEN", OPEN)
  # STEP 6. Go to Step 2.
  return None  # No more states on OPEN, and no goal reached.

def print_state_queue(name, q):
  print(name+" is now: ",end='')
  print(str(q))

def backtrace(S):
  global BACKLINKS
  path = []
  while S:
    path.append(S)
    S = BACKLINKS[S]
  path.reverse()
  print("Solution path: ")
  for s in path:
    print(s)
  return path
  
def report(open, closed, count):
  print("len(OPEN)="+str(len(open)), end='; ')
  print("len(CLOSED)="+str(len(closed)), end='; ')
  print("COUNT = "+str(count))

if __name__=='__main__':
  runAstar()

