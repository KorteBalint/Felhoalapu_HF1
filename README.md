# Felhoalapu_HF1

## Lab 3

My loadtest report can be found in [loadtest_report.md](loadtest/loadtest_report.md)
A summary of the configuration can be found in [scaling_configuration.md](loadtest/scaling_configuration.md)

I reran the test without raising AssertionErrors on registration:
[new locust data report](loadtest/Locust_2026-04-20-02h46_locustfile.py_https___photo-album-uyrobl-photo-album-uyrobl.apps.okd.fured.cloud.bme.hu.html)

Now the number of users is `30` and stable, pods scale to `5`, Failure ratio is `0.6`. But I will not update my report, because I think the lesson that I learnt is more important: **maybe it's not my app that's wrong but my test**.


Final Locust charts:

![locust_final_charts.png](img/lab3/locust_final_charts.png)


(If requested I will update [scaling_configuration.md](loadtest/scaling_configuration.md))

## Lab 2

Finished Django photo album implementation with:
- Photo upload and delete
- Photo listing with sorting by name or upload date
- Clickable list entries with image preview
- Auth (registration, login, logout)
- Restricted upload/delete to authenticated users only
- Deployed on BME OpenShift (OKD)
- Persistent database (PostgreSQL instead of in-memory storage)
- Separate app and database layers for scalable deployment
- Configured automatic GitHub-triggered build/deploy pipeline
- Nicer UI (by gpt-5.4 using [frontend-design skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md))


#### Pods running in OKD:
![pods_lab2.png](./img/pods_lab2.png)



### Documentation

#### Architecture

- Backend: Django web application, which implements the user interface and business logic.
- Data layer: PostgreSQL is used for persistent storage; uploaded images and their metadata are stored in the database.
- Runtime: the application runs in a container and is served by Gunicorn; database migrations are applied during startup. (not since Lab 3)
- Configuration: runtime settings are provided through environment variables, including secret key, host settings, and database connection parameters.

#### Tech Stack

- Django 6
- Python 3.13
- uv python package manager
- PostgreSQL
- Gunicorn
- Docker
- OpenShift / OKD
- GitHub Actions

#### OKD Deployment
- Hosting is defined through an OpenShift template describing the application resources.
- The deployment uses separate OpenShift objects for secrets, image stream, build configuration, deployment configuration, service, and public route.
- The web application and the database are separated into different layers, so the app container remains independent from the persistence service.
- External traffic enters through an HTTPS route, passes through the internal service, and reaches the Django container in the cluster.
- Health checks and resource limits are defined in the deployment to support stable runtime behavior.

#### GitHub Workflow
- A GitHub Actions workflow is triggered on pushes to the `master` branch.
- The first stage runs the Django test suite in CI before deployment is allowed.
- After successful validation, GitHub Actions connects to the BME OKD project and starts a new OpenShift build.
- OpenShift builds the image, updates the image stream, and rolls out the new application version automatically.
- Repository secrets and variables are used to keep platform credentials and deployment identifiers outside the source code.


## Lab 1

Django photo album implementation with:

- In-memory data store (no persistent database)
- No authentication
- Photo upload and delete
- Photo listing with sorting by name or upload date
- Clickable list entries with image preview
