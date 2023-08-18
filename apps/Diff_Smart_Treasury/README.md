# **DIFF Smart Treasury**
## About [Bank Data Validation](https://www.diff.com/sap-finance)

The DIFF Bank Data Validation Application is designed to ensure the highest quality and integrity of bank information within SAP systems, including S/4HANA and ECC. 
We prioritize robust controls on bank keys, vendor modifications, and the handling of obsolete vendors. Our application seamlessly integrates the capabilities of Google Cloud Platform Cortex Framework with SAP Fiori UI + React and standard APIs, offering a direct and efficient solution to enhance and validate your treasury master data.

While the solution is particularly beneficial for companies that rely on manual bank key creation and lack automated bank key update mechanisms, it also offers value to customers with existing automated bank key systems. Regardless of the level of automation, the software provides essential features for managing bank data effectively.

Overall, Bank Data Validation empowers Treasury and AP users to control, validate, and maintain accurate bank information, resulting in enhanced financial operations and reduced errors in payment processing.

For More Information visit our [YouTube Channel](https://www.youtube.com/playlist?list=PLlUWdSjbRKiNjm96SDYI66Y95pAbjGdPu).

## Index

1. [Features](#features)
2. [Process Flow](#process-flow)
3. [Architecture Diagram](#architecture-diagram)
4. [Technology Stack](#tech-stack)
5. [Prerequisites](#prerequisites)
6. [Setup Overview](#setup)
7. [Setup BackeEnd](#setup-be)
8. [Setup FrontEnd](#setup-fe)
9. [Contact Us](#contact-us)

## [Features](#features)
The objective of the app is to provide a tool to simplify certain controls on master data and allow users to take action in SAP:
- Bank key validation
--Identify duplicates or inconsistencies
-- Monitor usage of obsolete bank keys in Vendor BP and Treasury BP
- Vendor account modification review
-- Monitor changes to vendor accounts
- Obsolete vendor alert
-- Identify obsolete vendors with no invoices or payments in the last 24 months 

![APP Fiori UI](https://static.wixstatic.com/media/9d2d43_a272f620709d4913860341556284e8a9~mv2.png)

## [Process Flow](#process-flow)

The following is a high level representation of the App Process Flow:
- The stakeholders of the process
- Process & Process Steps
- Approvers
- Workflow

![Process Flow](https://static.wixstatic.com/media/9d2d43_a4636968e5de41d98b6c51a1e8128c56~mv2.png)

## [Architecture Diagram](#architecture-diagram)

The following is a high level representation of the App Architecture:
- Systems involved
- Google Cloud Platform Services
- Data Flow directions
- Communication Encryption Protocol (TLS)
- Tech Stack (React, UI5, Node.js, Docker)

![Overview Diagram](https://static.wixstatic.com/media/9d2d43_66b5a5aec45d4149b276c1743883b2ac~mv2.png)
Note: Seamless Integration: Syncing SAP Treasury Master Data to Google BigQuery, Paving the Way for Real-time Analysis in a dockerized App running on Cloud Run. Leveraging Cloud SQL to keep Activity & Approval logs.

## [Technology Stack](#tech-stack)

DIFF's Bank Data Validation App leverages the following stack:

| Tech | Description |
| ------ | ------ |
| BigQuery | Store SAP Treasury Master Data for real-time analysis and decision-making |
| Cloud SQL | Store Audit Logs and Approval logs from Users interactions |
| Cloud Run | Serverless platform that allows us to run the App Docker Containers (Front-End and Back-End) |
| React | React offers a component-based architecture, enabling fast rendering and a dynamic user experience |
| UI5 | SAP UI5 allows to maintain a SAP Fiori UX across the whole application for a seamless experience |
| Node.js | runtime environment enabling the App APIs and interfacing with SAP via RFC calls |
| SAP NetWeaver RFC SDK | Enables RFC calls via the node-rfc package |


## [Prerequisites](#prerequisites)
- This application requires to have data replicated from SAP Treasury in BigQuery. There is a variety of ways of doing this, in our case we leveraged the BigQuery Connector for SAP that build on top of the SAP LT Replication Server. For more information on this solution [visit](https://cloud.google.com/solutions/sap/docs/bq-connector/latest/planning#overview)
- In order to have a solution that doesn't require any additional add-on or OData API to be activated, we decided to go with an RFC approach to execute actions in the target SAP system. In order to do this, each customer will have to request to SAP via Service Request (using an S-User associated with the company) the [SAP NWRFC SDK](https://support.sap.com/en/product/connectors/nwrfcsdk.html). The NodeJS RFC connector relies on SAP NWRFC SDK and must be able to find the library files at runtime. Therefore, you might either install the SAP NWRFC SDK in the standard library paths of your system or install it in any location and tell the NodeJS connector where to look.

## [Setup](#setup) 
- For the files of this solution, please contact us at [sap-on-gcp@diff.com](mailto:sap-on-gcp@diff.com). In the subject of the email write Bank Data Validation and we will schedule a session with our SAP Treasury Solution Team.
- If you already have the files of this solution, follow the next steps.

### [BackEnd (API): bank-data-validation-api](#setup-be)

#### Node
Install the version specified in the .nvmrc file.
`nvm use`

#### Install dependencies
`npm i`

#### Env file
Create a .env file

```
API_PORT=XXXX

BIG_QUERY_PROJECT_ID='XXXXXXXXXXXXXXX'
BIG_QUERY_KEY_FILE_NAME='XXXXXXXXXXXXXX.json'

DB_HOST=XXXXXXX
DB_PORT=XXXXXXX
DB_USER=XXXXXXX
DB_PASS=XXXXXXX
DB_NAME=bdv
DB_ADAPTER=XXXXXXX

SAP_ASHOST=XXX.XXX.XXX.XXX
SAP_SYSNR=00
SAP_CLIENT=001
SAP_USER=XXXXX
SAP_PASS=XXXXX
SAP_LANG=EN
```

#### Build API

`npm run build`

#### Run API in *watch mode*

`npm run dev`

#### Modify Bank Validation tolerance
Update variable "COMPARE_TOLERANCE" in Google Cloud Run (Range from 0 to 1). Default is 0.5.

### [FrontEnd (Web): bank-data-validation-web](#setup-fe)

#### Build Web App 
`npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).
To learn React, check out the [React documentation](https://reactjs.org/).

## [Contact Us: Do you have questions?](#contact-us)
If you have questions, you would like to see a Demo or to discuss about how to build SAP Solutions leveraging Google Cloud Platform Cortex Framework (Data Foundation and/or App Layer) feel free to contact us at [sap-on-gcp@diff.com](mailto:sap-on-gcp@diff.com), 
You can also find us in [LinkedIn](https://www.linkedin.com/company/diff-consulting/) or in our [YouTube](https://www.youtube.com/playlist?list=PLlUWdSjbRKiNjm96SDYI66Y95pAbjGdPu) Channel where you can see Demos of this and other SAP + GCP Solutions leveraging Google Cloud Cortex Framework.