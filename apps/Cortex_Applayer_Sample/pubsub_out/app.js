/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use strict';
const express = require('express');
const { PubSub } = require('@google-cloud/pubsub');
const pbClient = new PubSub();

const topicName = process.env.PB_OUT_NAME || 'cortex-kmeans-clustering';

const app = express();
app.use(express.json());

app.get('/', (req, res) => {
  res.status(200).send('Ahoy mate!');
  return;
});

app.post('/', (req, res) => {
  console.log(JSON.stringify(req.body));

  if (!req.body) {
    res.status(400).send('Message content required');
  }

  async function publishMessage(data) {
    const dataBuffer = Buffer.from(data);

    const callback = (error, messageId) => {
      if (error) {
        console.error(`Received error while publishing: ${error}`);
        res.status(500).send(`${error}`);
      }

      console.log(`Message ${messageId} published.`);
      res.status(200).send(`${messageId}`);
    };

    try {
      const messageId = await pbClient
        .topic(topicName)
        .publishMessage({ data: dataBuffer }, callback);
    } catch (error) {
      console.error(`Received error while publishing: ${error.message}`);
      res.status(500).send(`${error.message}`);
    }
  }

  publishMessage(req.body);
});

module.exports = app;
