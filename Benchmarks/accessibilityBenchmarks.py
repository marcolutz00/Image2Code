import json
import os

SEVERITY = {"minor": 1, "moderate": 3, "serious": 6, "critical": 10}
THRESHOLD_HIGH_IR = 0.25
THRESHOLD_LOW_IR = 0.1
# 0.3 corresponds to only moderate or minor issues
THRESHOLD_HIGH_IWIR = 0.6
THRESHOLD_LOW_IWIR = 0.3

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
        if inaccessibility_rate > THRESHOLD_HIGH_IR and impact_weighted_inaccessibility_rate > THRESHOLD_HIGH_IWIR:
            return "Red"
        elif inaccessibility_rate <= THRESHOLD_LOW_IR and impact_weighted_inaccessibility_rate <= THRESHOLD_LOW_IWIR:
            return "Green"
        else:
            return "Yellow"