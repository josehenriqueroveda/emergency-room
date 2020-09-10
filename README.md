# 🏥 Emergency Room

A model that simulates the flow of patients in a hospital emergency room using [SIMPY](https://simpy.readthedocs.io/en/latest/)

## How does it works?

* The model mimics the random arrival of patients at an emergency room (ER). 
* The patients are assessed as being low, medium or high priority. 
* Higher priority patients are always selected next (keeping the lowest priority patient who is already being consulted by a doctor).


## Usage


```bash
python emergency-room.py
```

The following inputs will appear to be filled:
1. Days for the simulation
2. Average patient arrival time in minutes
3. Number of doctors
4. Average time in medical consultation (minutes)
5. Standard deviation in time in medical consultation (minutes)

![](https://raw.githubusercontent.com/josehenriqueroveda/emergency-room/master/usage.png)

## Output

The simulation will generate 3 graphs:
1. The first with the relationship between each patient (with their priority) and the waiting time.
2. The second graph shows the number of patients waiting during the days
3. Finally, a graph of the occupation of doctors during the days of the simulation is shown

![](https://raw.githubusercontent.com/josehenriqueroveda/emergency-room/master/Figure_1.png)

**Liked it?**
Find me on [LinkedIn](https://www.linkedin.com/in/jhroveda/)