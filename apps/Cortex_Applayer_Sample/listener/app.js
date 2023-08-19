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
const app = express();
const dalSvc = process.env.DAL_SVC.trim();
const outSvc = process.env.PBOUT_SVC.trim();
const { GoogleAuth } = require('google-auth-library');
const { URL } = require('url');
const auth = new GoogleAuth();


app.use(express.json());

app.get('/', (req, res) => {
  res.status(200).send('Hi there');
  return;
});

app.post('/', (req, res) => {
  if (!req.body) {
    const msg = 'Invalid request - no body';
    console.log(`Error receving REQUEST: ${msg}`);
    res.status(400).send(`Bad Request: ${msg}`);
    return;
  }

  const attribs = req.body;


  async function getClustering(dalSvc, attribs) {
    const reqBody = {
        project: attribs.project,
        location : attribs.location,
        ml_dataset : attribs.ml_dataset,
        reporting_dataset : attribs.reporting_dataset,
        limit: attribs.limit,
      // TODO: pass query parameters
    };

    try {
      const targetSvc = new URL(dalSvc).origin;
      console.log(`targetSvc = ${targetSvc}`);

      const client = await auth.getIdTokenClient(targetSvc);
      const { status, data } = await client.request({
        url: dalSvc,
        method: 'POST',
        data: reqBody,
      });

      if (!data || data.length == 0) {
        throw new Error('No rows returned');
      }

      const gotchu = data;

      console.log(`Status: ${status} - received rows: ${JSON.stringify(gotchu)}`);

      // console.log(`Rows is: ${JSON.stringify(data)}`);
      // data.forEach((row) =>
      //   // console.log(`${row.sku}: ${row.ValuatedStock} ${row.UoM}`));
      //   console.log(row)
      // );
      return gotchu;
    } catch (err) {
      console.log(`Error while calling DAL: ${err}`);
    }
  }

  async function sendOut(outSvc) {
    try {

      const gotchu = await getClustering(dalSvc, attribs);

      console.log(`gotchu = ${JSON.stringify(gotchu)}`);

      const targetAudience = new URL(outSvc).origin;
      console.log(`targetAudience = ${targetAudience}`);

      const client = await auth.getIdTokenClient(targetAudience);
      const { status, data } = await client.request({
        url: outSvc,
        method: 'POST',
        data: gotchu,
      });

      console.log(`Pubsub Out Status Resp: ${status} - ${data}`);
      res.status(200).send();
      return;
    } catch (err) {
      console.log(`Error while posting message to pubsub out: ${err}`);
      res.status(500).send(err+ ' Consider add parameter `limit` if there are too many results.');
      return;
    }
  }

  sendOut(outSvc);
});

module.exports = app;