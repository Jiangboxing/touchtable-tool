## How to run
We use docker to containerize this application. Therefore it is rather simple to get up and running.

1. Rename example.env to .env
2. Change the variables to your situation
3. npm run start

If everything is good you have a non deamonized docker containing up and running. If you want to have it run as a deamon you should call <code> npm run start:deamon </code> instead of <code> npm run start </code>