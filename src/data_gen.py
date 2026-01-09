
import pandas as pd
import numpy as np
import os
import random

def generate_it_project_data(num_samples=1000):
    """
    Generates synthetic data for IT/CS projects to predict Timeline Delay and Cost Overrun.
    Now includes rich natural language descriptions for NLP training.
    """
    np.random.seed(42)
    random.seed(42)

    project_types = ['Web App', 'Mobile App', 'Enterprise Software', 'AI/ML Project', 'SaaS Platform']
    
    # Enhanced Description Generators
    templates = {
        'Web App': [
            "Build a {scale} e-commerce platform using {stack} with {feature}.",
            "Develop a {scale} corporate website utilizing {stack} and {feature}.",
            "Create a customer portal with {stack} integration and {feature}."
        ],
        'Mobile App': [
            "Develop a {scale} iOS and Android app using {stack} featuring {feature}.",
            "Build a {stack} based fitness tracking app with {feature}.",
            "Create a cross-platform solution using {stack} with {feature}."
        ],
        'Enterprise Software': [
            "Implement a {scale} ERP system using {stack} with complex {feature}.",
            "Migrate legacy systems to {stack} architecture including {feature}.",
            "Develop an internal HR management tool with {stack} and {feature}."
        ],
        'AI/ML Project': [
            "Train a {scale} deep learning model using {stack} for {feature}.",
            "Implement computer vision pipeline with {stack} and {feature}.",
            "Build a predictive analytics dashboard using {stack} and {feature}."
        ],
        'SaaS Platform': [
            "Architect a multi-tenant SaaS using {stack} with {feature} capability.",
            "Develop a cloud-native subscription platform on {stack} featuring {feature}.",
            "Build a scalable API marketplace using {stack} and {feature}."
        ]
    }

    stacks = ['React/Node.js', 'Python/Django', 'Java Spring Boot', 'Flutter', 'AWS/Lambda', 'Kubernetes', 'TensorFlow', 'PostgreSQL']
    features = [
        "real-time notifications", "AI-driven insights", "blockchain integration", 
        "legacy data migration", "high-frequency trading modules", "payment gateway integration",
        "GDPR compliance tools", "advanced biometric authentication", "IoT sensor data processing"
    ]
    scales = ["small-scale", "medium-scale", "large-scale enterprise", "global", "high-performance"]

    data_rows = []

    for _ in range(num_samples):
        p_type = np.random.choice(project_types)
        
        # Generate NLP Description
        template = random.choice(templates[p_type])
        description = template.format(
            scale=random.choice(scales),
            stack=random.choice(stacks),
            feature=random.choice(features)
        )
        
        # Keyword based complexity boos
        complexity_boost = 0
        if "blockchain" in description or "AI" in description or "legacy" in description:
            complexity_boost += 2
        if "global" in description or "high-performance" in description:
            complexity_boost += 1
            
        base_complexity = np.random.randint(1, 9)
        final_complexity = min(10, base_complexity + complexity_boost)

        data_rows.append({
            'project_type': p_type,
            'project_description': description, # NEW FIELD
            'complexity_score': final_complexity,
            'number_of_developers': np.random.randint(2, 50),
            'team_experience_rating': np.random.randint(1, 6),
            'dependency_delay_days': np.random.randint(0, 30),
            'resource_availability_ratio': np.random.uniform(0.5, 1.0),
            'labour_cost_index': np.random.uniform(1.0, 3.0),
            'historical_delay_days': np.random.randint(0, 20)
        })
    
    df = pd.DataFrame(data_rows)

    # --- Feature Engineering Targets ---
    
    noise_delay = np.random.normal(0, 5, num_samples)
    noise_cost = np.random.normal(0, 5, num_samples)

    df['actual_delay_days'] = (
        (df['complexity_score'] * 4.0) + 
        (df['dependency_delay_days'] * 1.2) - 
        (df['team_experience_rating'] * 3.0) - 
        (df['number_of_developers'] * 0.5) + 
        (df['historical_delay_days'] * 0.4) -
        (df['resource_availability_ratio'] * 15.0) +
        30 + 
        noise_delay
    )
    df['actual_delay_days'] = df['actual_delay_days'].apply(lambda x: max(0, int(x)))

    df['cost_overrun_percent'] = (
        (df['actual_delay_days'] * 0.5) + 
        (df['complexity_score'] * 1.5) +
        (df['labour_cost_index'] * 5.0) -
        (df['team_experience_rating'] * 2.0) - 
        (df['resource_availability_ratio'] * 10.0) +
        10 +
        noise_cost
    )
    df['cost_overrun_percent'] = df['cost_overrun_percent'].apply(lambda x: max(0, round(x, 2)))

    # --- Generate Suggestion Labels (Classification Target) ---
    def get_suggestion(row):
        if row['complexity_score'] >= 8:
            return "Adopt Microservices & Strict CI/CD"
        elif row['team_experience_rating'] <= 2:
            return "Hire Senior Consultants & Increase Code Reviews"
        elif row['dependency_delay_days'] > 15:
            return "Negotiate Vendor SLAs &Buffer Schedule"
        elif row['resource_availability_ratio'] < 0.7:
            return "Increase Resource Allocation by 20%"
        elif row['project_type'] == 'AI/ML Project':
            return "Invest in GPU Compute & MLOps Pipeline"
        else:
            return "Standard Agile Process Optimization"

    df['primary_recommendation'] = df.apply(get_suggestion, axis=1)

    # Save
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/it_projects.csv', index=False)
    print(f"Generated {num_samples} rows of IT Project data with Suggestions to data/it_projects.csv")

if __name__ == "__main__":
    generate_it_project_data()
