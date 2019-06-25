# accountabot
Accountability via an email-bot - it sort of works is quite insecure and is questionably architected, but doesn't cost much to run and maybe does the job?  

Currently hosted at https://us-central1-accountabot.cloudfunctions.net/home

### Deployment
Functions can be updated individually via e.g. 

```
cd cloud_functions/send_summary_email
gcloud functions deploy send_summary_email --source . --runtime python37
```
