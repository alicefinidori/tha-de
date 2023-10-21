from locust import HttpUser, task, between


class ApiUser(HttpUser):
    wait_time = between(1, 5)  # Randomized wait time between tasks

    @task
    def call_api(self):
        response = self.client.get(
            '/default/campaigns/12',  # Replace with your API Gateway endpoint
        )
        assert response.status_code == 200
