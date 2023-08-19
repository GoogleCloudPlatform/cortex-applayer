*******************************************************************************
* Copyright 2023 Google LLC
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     https://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************

REPORT zgoog_r_cortex_kmeans_clust.

PARAMETERS: p_key   TYPE /goog/keyname,
            p_subsc TYPE string LOWER CASE.

CLASS lcl_main DEFINITION.

  PUBLIC SECTION.

    TYPES:
      BEGIN OF t_centroid_dist,
        centroid_id TYPE i,
        distance    TYPE i,
      END OF t_centroid_dist,

      tt_centroid_dist TYPE STANDARD TABLE OF t_centroid_dist WITH DEFAULT KEY.


    TYPES:
      BEGIN OF t_kmeans_result,
        centroid_id                TYPE int4,
        nearest_centroids_distance TYPE flag,
        vbap_kunnr                 TYPE string,
        languagekey_spras          TYPE string,
        countrykey_land1           TYPE string,
        avg_item_price             TYPE bapi_price,
        avg_item_count             TYPE bapi_price,
        order_count                TYPE int4,
      END OF t_kmeans_result,

      tt_kmeans_result TYPE STANDARD TABLE OF t_kmeans_result.

    TYPES:
      BEGIN OF t_kmeans_result_out,
        centroid_id       TYPE int4,
        vbap_kunnr        TYPE string,
        languagekey_spras TYPE string,
        countrykey_land1  TYPE string,
        avg_item_price    TYPE bapi_price,
        avg_item_count    TYPE bapi_price,
        order_count       TYPE int4,
      END OF t_kmeans_result_out,

      tt_kmeans_result_out TYPE STANDARD TABLE OF t_kmeans_result_out.

    CLASS-METHODS: execute.

ENDCLASS.

START-OF-SELECTION.

  lcl_main=>execute( ).

CLASS lcl_main IMPLEMENTATION.

  METHOD execute.

    DATA:
      lo_client             TYPE REF TO /goog/cl_pubsub_v1,
      lv_p_projects_id      TYPE string,
      lv_p_subscriptions_id TYPE string,
      ls_input              TYPE /goog/cl_pubsub_v1=>ty_026,
      ls_output             TYPE /goog/cl_pubsub_v1=>ty_027,
      ls_message            TYPE /goog/cl_pubsub_v1=>ty_029,
      ls_kmeans_result      TYPE t_kmeans_result,
      ls_kmeans_result_out  TYPE t_kmeans_result_out,
      lv_ret_code           TYPE i,
      lv_err_text           TYPE string,
      ls_err_resp           TYPE /goog/err_resp,
      lv_msg                TYPE string,
      lo_exception          TYPE REF TO /goog/cx_sdk.

    TRY.
        CREATE OBJECT lo_client
          EXPORTING
            iv_key_name = p_key.
      CATCH /goog/cx_sdk INTO lo_exception.
        lv_msg = lo_exception->get_text( ).
        MESSAGE lv_msg TYPE 'S' DISPLAY LIKE 'E'.
        RETURN.
    ENDTRY.

    TRY.

        lv_p_projects_id = lo_client->gv_project_id.
        lv_p_subscriptions_id = p_subsc.
        ls_input-max_messages = 50.


        CALL METHOD lo_client->pull_subscriptions
          EXPORTING
            iv_p_projects_id      = lv_p_projects_id
            iv_p_subscriptions_id = lv_p_subscriptions_id
            is_input              = ls_input
          IMPORTING
            es_output             = ls_output
            ev_ret_code           = lv_ret_code
            ev_err_text           = lv_err_text
            es_err_resp           = ls_err_resp.


      CATCH /goog/cx_sdk INTO lo_exception.
        lv_msg = lo_exception->get_text( ).
        MESSAGE lv_msg TYPE 'S' DISPLAY LIKE 'E'.
        RETURN.
    ENDTRY.

    DATA: lt_result TYPE tt_kmeans_result_out.

    IF lo_client->is_success( lv_ret_code ) = abap_true.
      LOOP AT ls_output-received_messages INTO ls_message.
        lv_msg = cl_http_utility=>decode_base64( encoded = ls_message-message-data ).

        CLEAR: ls_kmeans_result, ls_kmeans_result_out.

        CALL METHOD /ui2/cl_json=>deserialize
          EXPORTING
            json = lv_msg
          CHANGING
            data = ls_kmeans_result.

        ls_kmeans_result_out = CORRESPONDING #( ls_kmeans_result ).

        APPEND ls_kmeans_result_out TO lt_result.
      ENDLOOP.


      cl_demo_output=>display(
        data =  lt_result
        name  = 'Cortex Kmeans Clustering Result' ).
    ELSE.
      lv_msg = lv_ret_code && ':' && lv_err_text.
      cl_demo_output=>display( lv_msg ).
    ENDIF.

  ENDMETHOD.

ENDCLASS.
