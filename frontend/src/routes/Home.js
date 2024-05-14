import React from "react";
import { Button } from 'antd-mobile';
import { Input, Form } from 'antd';
import { useIntl } from 'react-intl';
import { useNavigate, useLocation } from "react-router-dom";

import axios from '../util/Api.js'
import PaymentOptions from '../components/PaymentOptions.js'

export default function Home() {
  const [form] = Form.useForm();
  const { evseId, message } = { evseId: null, message: null };
  const intl = useIntl();
  const navigate = useNavigate();
  const location = useLocation();

  React.useEffect(() => {
    /* Setting evseId and errorMsg if we got forwarded from Checkout */
    const { evseId, errMsg } = location.state ? location.state : { };
    if(evseId) {
      form.setFields([ {name: 'evseId', errors: [intl.formatMessage({ id: errMsg })], value: evseId } ]);
    }

  }, []);

  const onFinish = (values) => {
    axios.get(`evses/${values.evseId}`).then(({data}) => {
      // Check if location given, else show message
      if(data.id) {
        navigate(
          '/checkout/' + values.evseId, 
          // { state: { locationData: {...data.data} } }
        );
      }
      else {
        form.setFields([ {name: 'evseId', errors: [intl.formatMessage({ id: data.message ? data.message : "global.error.generic" })]} ]);
      }
    }).catch(error => {
      form.setFields([ {name: 'evseId', errors: [intl.formatMessage({ id: error.response?.data?.detail ? error.response.data.detail : "global.error.generic" })]} ]);
    });
  }

  return (
    <div className="page-container page-container-home">
      <h1>SCAN<span style={{marginLeft: '30px',}}> </span>PAY</h1>
      <h1>CHARGE</h1>
      <div className="div-with-margin text-align-center">
        {intl.formatMessage({id: "home.subheading" })}
      </div>
      <div className="div-with-margin width-100">
        <PaymentOptions />
      </div>
      <div className="div-with-margin text-align-center">
        {intl.formatMessage({id: "home.instructions" })}
      </div>
      <Form name="openinghours" onFinish={onFinish} form={form} className="width-100" labelCol={{ span: 0 }} wrapperCol={{ span: 24 }}>
        <div className="div-with-margin width-100">
          <Form.Item name="evseId" label="EVSE ID" rules={[{ required: true }]}>
            <Input
              style={{width: '100%'}}
              size="large"
              placeholder="DE*CPO*E1234567"
            />
          </Form.Item>
        </div>
        <div className="div-with-margin text-align-center">
          <Button type="submit" >{intl.formatMessage({id: "global.continue" })}</Button>
        </div>
      </Form>
    </div>
  );
}
