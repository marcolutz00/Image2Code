import json
import os

SEVERITY = {"minor": 1, "moderate": 3, "serious": 6, "critical": 10}
THRESHOLD_HIGH = 0.25
THRESHOLD_LOW = 0.1

class AccessibilityBenchmarks:

    def calculate_inaccessibility_rate(self, amount_failed_nodes, total_nodes):
        '''
            Calculation of the inaccessibility rate based on the number of failed 
            nodes without impact

        '''
        return amount_failed_nodes / total_nodes if total_nodes > 0 else 0


    def calculate_impact_weighted_inaccessibility_rate(self, amount_critical, amount_serious, amount_moderate, amount_minor):
        '''
            Calculation of the impact-weighted inaccessibility rate based on the number of failed nodes 
            while considering the severity of the issues

        '''
        return (
            (amount_critical * SEVERITY["critical"] +
            amount_serious * SEVERITY["serious"] +
            amount_moderate * SEVERITY["moderate"] +
            amount_minor * SEVERITY["minor"])
            / ((amount_critical + amount_serious + amount_moderate + amount_minor) * SEVERITY["critical"])
            if (amount_critical + amount_serious + amount_moderate + amount_minor) > 0
            else 0
        )


    def calculate_status(self, inaccessibility_rate, impact_weighted_inaccessibility_rate):
        '''
            Final status:     IR          IW-IR         Interpretation
            Red:              high        high          Many issues, many serious/critical
            Yellow:           high        low           Many issues, but not serious/critical
            Yellow:           low         high          Few issues, but serious/critical
            Green:            low         low           Few issues, few serious/critical

        '''
        if inaccessibility_rate > THRESHOLD_HIGH and impact_weighted_inaccessibility_rate > THRESHOLD_HIGH:
            return "Red"
        elif inaccessibility_rate < THRESHOLD_HIGH and impact_weighted_inaccessibility_rate < THRESHOLD_LOW:
            return "Green"
        else:
            return "Yellow"