# aura_interview_ek

**The file main.py accomplishes the following tasks:** 

1- Hosts a static website in AWS using CDKTF.

2- Routable via DNS (I do not have a custom domain that I can use, so it's using Cloudfront's default distribution domain name given by AWS).

3- It's routable via HTTPS only.

4- It only allows traffic from my IP.

5- It's creatable via CDKTF IAC.

6- The Static site is an index.html with a "Hello World".

7- It also includes the timestamp of when it was deployed as part of the html content.

**Site:** 

The site can be accessed from my computer by going to:

https://di5xkhz3q1y0j.cloudfront.net

**Screenshots:** 

I am attaching below a screenshot of the site accessible from my IP:

<img width="1057" alt="Screenshot 2025-05-17 at 10 08 14 AM" src="https://github.com/user-attachments/assets/ebf49596-c5ee-4014-a738-4d915380543a" />



And this is the result when the site is accessed via another IP that's not mine:

![Screenshot 2025-05-17 101723](https://github.com/user-attachments/assets/33e19b77-8d97-4eb2-b0af-321d115c28b2)
