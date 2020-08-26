import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt


class EmergencyRoom:
    # Time in minutes
    # Simulation run time and warm-up (warm-up is time before audit results are collected)
    simulation_time = 7200
    warm_up = 1440

    # Average time between patients arriving
    inter_arrival_time = 8

    # Number of doctors in ER
    n_doctors = 3

    # Time between audits
    audit_interval = 100

    # Average and standard deviation of time doctors spends with patients in ER
    appointment_mean = 15
    appointment_std = 7

    # Lists to store audit results
    audit_time = []
    audit_patients_in_ER = []
    audit_patients_waiting = []
    audit_patients_waiting_p1 = []
    audit_patients_waiting_p2 = []
    audit_patients_waiting_p3 = []
    audit_reources_used = []

    # Dataframes to store results 
    patient_queuing_results = pd.DataFrame(
        columns=['priority', 'q_time', 'consult_time'])
    results = pd.DataFrame()

    # Number of patients on simulation
    patient_count = 0

   # Total patients waiting and priority
    patients_waiting = 0
    patients_waiting_by_priority = [0, 0, 0]


class Model:
    def __init__(self):
        self.env = simpy.Environment()


    def build_audit_results(self):
        EmergencyRoom.results['time'] = EmergencyRoom.audit_time
        EmergencyRoom.results['patients in ER'] = EmergencyRoom.audit_patients_in_ER
        EmergencyRoom.results['all patients waiting'] = \
            EmergencyRoom.audit_patients_waiting
        EmergencyRoom.results['high priority patients waiting'] = \
            EmergencyRoom.audit_patients_waiting_p1
        EmergencyRoom.results['medium priority patients waiting'] = \
            EmergencyRoom.audit_patients_waiting_p2
        EmergencyRoom.results['low priority patients waiting'] = \
            EmergencyRoom.audit_patients_waiting_p3
        EmergencyRoom.results['resources occupied'] = \
            EmergencyRoom.audit_reources_used


    def chart(self):
        fig = plt.figure(figsize=(12, 4.5), dpi=75)
        # Create charts side by side

        # Figure 1: patient perspective results
        ax1 = fig.add_subplot(131)  # 1 row, 3 cols, chart position 1
        x = EmergencyRoom.patient_queuing_results.index
        # Chart loops through 3 priorites
        markers = ['o', 'x', '^']
        for priority in range(1, 4):
            x = (EmergencyRoom.patient_queuing_results
                 [EmergencyRoom.patient_queuing_results['priority'] ==
                  priority].index)

            y = (EmergencyRoom.patient_queuing_results
                 [EmergencyRoom.patient_queuing_results['priority'] ==
                  priority]['q_time'])

            ax1.scatter(x, y,
                        marker=markers[priority - 1],
                        label='Priority ' + str(priority))

        ax1.set_xlabel('Patient ID')
        ax1.set_ylabel('Waiting time in minutes')
        ax1.legend()
        ax1.grid(True, which='both', lw=1, ls='--', c='.75')

        # Figure 2: ER queuing results
        ax2 = fig.add_subplot(132)  # 1 row, 3 cols, chart position 2
        x = EmergencyRoom.results['time']/1440 #convert to days
        y1 = EmergencyRoom.results['high priority patients waiting']
        y2 = EmergencyRoom.results['medium priority patients waiting']
        y3 = EmergencyRoom.results['low priority patients waiting']
        y4 = EmergencyRoom.results['all patients waiting']
        ax2.plot(x, y1, marker='o', label='High priority')
        ax2.plot(x, y2, marker='x', label='Medium priority')
        ax2.plot(x, y3, marker='^', label='Low priority')
        ax2.plot(x, y4, marker='s', label='All')
        ax2.set_xlabel('Day')
        ax2.set_ylabel('Patients waiting')
        ax2.legend()
        ax2.grid(True, which='both', lw=1, ls='--', c='.75')

        # Figure 3: ER doctors in attendance
        ax3 = fig.add_subplot(133)  # 1 row, 3 cols, chart position 3
        x = EmergencyRoom.results['time']/1440
        y = EmergencyRoom.results['resources occupied']
        ax3.plot(x, y, label='Doctors in attendance')
        ax3.set_xlabel('Day')
        ax3.set_ylabel('Doctors in attendance')
        ax3.legend()
        ax3.grid(True, which='both', lw=1, ls='--', c='.75')

        # Create plot
        plt.tight_layout(pad=3)
        plt.show()


    def perform_audit(self):
        # Delay before first aurdit if length of warm-up
        yield self.env.timeout(EmergencyRoom.warm_up)
        # The trigger repeated audits
        while True:
            # Record time
            EmergencyRoom.audit_time.append(self.env.now)
            # Record patients waiting
            EmergencyRoom.audit_patients_waiting.append(
                EmergencyRoom.patients_waiting)
            EmergencyRoom.audit_patients_waiting_p1.append(
                EmergencyRoom.patients_waiting_by_priority[0])
            EmergencyRoom.audit_patients_waiting_p2.append(
                EmergencyRoom.patients_waiting_by_priority[1])
            EmergencyRoom.audit_patients_waiting_p3.append(
                EmergencyRoom.patients_waiting_by_priority[2])
            # Record patients waiting by asking length of dict of all patients
            EmergencyRoom.audit_patients_in_ER.append(len(Patient.all_patients))
            # Record resources occupied
            EmergencyRoom.audit_reources_used.append(
                self.doc_resources.docs.count)
            # Trigger next audit after interval
            yield self.env.timeout(EmergencyRoom.audit_interval)


    def run(self):
        # Set up resources
        self.doc_resources = Resources(self.env, EmergencyRoom.n_doctors)

        # Initialise processes
        self.env.process(self.trigger_admissions())
        self.env.process(self.perform_audit())

        # Run
        self.env.run(until=EmergencyRoom.simulation_time)

        # End of simulation, build and save results
        EmergencyRoom.patient_queuing_results.to_csv('patient results.csv')
        self.build_audit_results()

        EmergencyRoom.results.to_csv('operational results.csv')
        # Plot results
        self.chart()


    def doctor_appointment(self, p):
        with self.doc_resources.docs.request(priority=p.priority) as req:
            EmergencyRoom.patients_waiting += 1
            EmergencyRoom.patients_waiting_by_priority[p.priority - 1] += 1

            # Wait for doctors to become available
            yield req

            # Doctor available -> Record time that appointment starts
            p.time_see_doc = self.env.now

            # Ppatient queuing time
            p.queuing_time = self.env.now - p.time_in

            # Reduce the number of patients waiting
            EmergencyRoom.patients_waiting_by_priority[p.priority - 1] -= 1
            EmergencyRoom.patients_waiting -= 1

            # List with patient priority and queuing
            _results = [p.priority, p.queuing_time]

            # Appointment time required
            yield self.env.timeout(p.consulation_time)

            # At end of appointment add the time spent
            _results.append(self.env.now - p.time_see_doc)

            # Record results data if warm-up complete
            if self.env.now >= EmergencyRoom.warm_up:
                EmergencyRoom.patient_queuing_results.loc[p.id] = _results

            # Delete patient (removal from patient dictionary removes only
            # reference to patient and Python then automatically cleans up)
            del Patient.all_patients[p.id]


    def trigger_admissions(self):
       # Generating new patients 
        while True:
            # Initialise new patient
            p = Patient(self.env)
            # Add patient to dictionary of patients
            Patient.all_patients[p.id] = p
            # Pass patient to doctor_appointment method
            self.env.process(self.doctor_appointment(p))
            # Sample time for next asmissions
            next_admission = random.expovariate(
                1 / EmergencyRoom.inter_arrival_time)
            # Schedule next admission
            yield self.env.timeout(next_admission)


class Patient:
    all_patients = {}

    def __init__(self, env):
        # Increment number of patients
        EmergencyRoom.patient_count += 1

        # Set patient id and priority
        self.id = EmergencyRoom.patient_count
        self.priority = random.randint(1, 3)

        # Set appointment time by random normal distribution. If value <0 then set to 0
        self.consulation_time = random.normalvariate(
            EmergencyRoom.appointment_mean, EmergencyRoom.appointment_std)
        self.consulation_time = 0 if self.consulation_time < 0 \
            else self.consulation_time

        # Initial queuing time as zero
        self.queuing_time = 0

        # record simulation time patient enters simulation
        self.time_in = env.now

        # Set up variables to record simulation appointment time, then exit simulation
        self.time_see_doc = 0
        self.time_out = 0


class Resources:
    def __init__(self, env, n_doctors):
        self.docs = simpy.PriorityResource(env, capacity=n_doctors)


# Run model 
if __name__ == '__main__':
    # Initialise model environment
    model = Model()
    # Run model
    model.run()