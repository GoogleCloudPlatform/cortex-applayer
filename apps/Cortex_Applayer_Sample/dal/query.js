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
app.use(express.json());

const { BigQuery } = require('@google-cloud/bigquery');
const client = new BigQuery();

app.get('/', (req, res) => {
  res.status(200).send('Hi there');
  return;
});

app.post('/', (req, res) => {
  async function getClustering(req) {
    const project = req.body.project;
    const location = req.body.location;
    const ml_dataset = req.body.ml_dataset;
    const reporting_dataset = req.body.reporting_dataset;
    const limit = req.body.limit;

    const query = `SELECT * FROM
      ML.PREDICT(MODEL \`${project}.${ml_dataset}.clustering_nmodel\`, (
      SELECT
      vbap_kunnr,
      LanguageKey_SPRAS,
      CountryKey_LAND1,
      avg(avg_item) AS avg_item_price,
      avg(item_count) AS avg_item_count,
      sum(order_counter) AS order_count FROM
      (
      SELECT
      SoldtoParty_KUNNR AS vbap_kunnr,
      SalesDocument_VBELN,
      LanguageKey_SPRAS,
      CountryKey_LAND1,
      1 AS order_counter,
      avg(NetPrice_NETWR) AS avg_item,
      sum(counter) AS item_count
      FROM (
      SELECT
      SO.SoldtoParty_KUNNR,
      SO.NetPrice_NETWR,
      SO.SalesDocument_VBELN,
      CM.CountryKey_LAND1,
      CM.LanguageKey_SPRAS,
      1 AS counter
      FROM
      \`${project}.${reporting_dataset}.SalesOrders\` AS SO
      INNER JOIN \`${project}.${reporting_dataset}.CustomersMD\` AS CM
      ON
      SO.Client_MANDT = CM.Client_MANDT
      AND SO.SoldtoParty_KUNNR = CM.CustomerNumber_KUNNR )
      GROUP BY vbap_kunnr, SalesDocument_VBELN, LanguageKey_SPRAS, CountryKey_LAND1
      ORDER BY SalesDocument_VBELN )
      GROUP BY vbap_kunnr, LanguageKey_SPRAS, CountryKey_LAND1
      )
      )` +
      ( typeof limit !== "undefined" ? ` limit ${limit}` : "");

    const options = {
      query: query,
      location: 'US',
    };

    try {
      const [rows] = await client.query(options);

      if (rows.length == 0) {
        console.log(`No rows returned`);
        res.status(204).send();
        return;
      }

      res.status(200).send(rows);
      return;
    } catch (error) {
      console.log(`Something went wrong: ${error}`);
      res.status(500).send(error);
      return;
    }
  }

  getClustering(req);
});

module.exports = app;

