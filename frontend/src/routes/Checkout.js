import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { Card, Button, Checkbox } from 'antd-mobile';
import { Skeleton, Modal } from 'antd';

import PaymentCardImg from '../assets/images/Payment_page_card.png';
import PaymentOptions from '../components/PaymentOptions.js';

import axios from '../util/Api.js';
import getConnectorPowerKw from '../util/ConnectorCalculatePower.js';
import { getLocationData } from '../util/getLocationData.js';

const httpProtocol = process.env.REACT_APP_SSL_ENABLED ? 'https' : 'http';
const currencies = {
  EUR: '€',
  USD: '$',
};

export default function Checkout(props) {
  const [state, setState] = React.useState({
    power_type: null,
    max_voltage: null,
    max_amperage: null,
    address: null,
    postalCode: null,
    city: null,
    state: null,
    country: null,
    operator: null,
    payment_terms_conditions: null,
    tariff_data: null,
    errMsg: null,
    taChecked: false,
    loading: false,
    initializing: true,
    status: 'UNKNOWN',
    modalVisible: false,
  });
  const navigate = useNavigate();
  const intl = useIntl();
  const { evseId } = useParams();

  React.useEffect(() => {
    if (evseId) {
      axios
        .get(`evses/${evseId}`)
        .then(async ({ data }) => {
          // Check if location given, else forward to home
          if (data.id) {
            const location_data = await getLocationData(data);
            // const connector_data = data.connectors?.[0]
            // delete data.connectors;

            // const location_data = (await axios.get(`locations/${data.location_id}`)).data;
            // const operator = location_data.operator?.name;
            // delete location_data.operator;
            // // const operator_data = (await axios.get(`operators/${location_data.operator_id}`)).data;
            // const tariff_data = (await axios.get(`tariffs/${connector_data.tariff_id}`)).data;
            // delete tariff_data.id;

            setLocationData(location_data);
          } else {
            // Navigate to home with error
            navigate('/', {
              state: {
                evseId: evseId,
                errMsg: data.message ? data.message : 'global.error.generic',
              },
            });
          }
        })
        .catch((e) => {
          // Navigate to home with error
          navigate('/', {
            state: { evseId: evseId, errMsg: 'global.error.generic' },
          });
        });
    } else {
      // Navigate to home if no location data is given
      navigate('/');
    }
  }, []);

  const setLocationData = (location) => {
    setState({ ...state, ...location, initializing: false });
  };

  const onCheckout = (e) => {
    setState({ ...state, errMsg: null });

    // Check if TA accepted, if not show error
    if (!state.taChecked) {
      setState({
        ...state,
        errMsg: intl.formatMessage({ id: 'checkout.error.tanotaccepted' }),
      });
      return false;
    }

    // TA accpeted, process checkout
    setState({ ...state, loading: true });
    axios
      .post(`checkouts/`, {
        evse_id: evseId,
        success_url: `${httpProtocol}://${window.location.host}/charging/${evseId}`,
        cancel_url: `${httpProtocol}://${window.location.host}/checkout/${evseId}`,
      })
      .then(({ data }) => {
        // Check if checkout given,
        if (data?.url) {
          window.location.replace(data.url);
        } else
          setState({
            ...state,
            loading: false,
            errMsg: intl.formatMessage({ id: 'global.error.generic' }),
          });
      })
      .catch((e) => {
        setState({
          ...state,
          loading: false,
          errMsg: intl.formatMessage({ id: 'global.error.generic' }),
        });
      });
  };

  const get_price = (net_price) => {
    const price = net_price * (1 + state.tariff_data?.tax_rate / 100);
    return price.toFixed(2);
  };

  return (
    <div className="page-container" style={{ height: '100%' }}>
      <div style={{ padding: '5px', width: '100%' }}>
        <Skeleton active loading={state.initializing}>
          {/* Top row */}
          <div className="checkout-top-container">
            <div>{evseId}</div>
            <div>|</div>
            <div>{state.power_type}</div>
            <div>|</div>
            <div>
              max.{' '}
              {getConnectorPowerKw(
                state.max_voltage,
                state.max_amperage,
                state.power_type,
              )}{' '}
              kW
            </div>
          </div>
          <div
            className="checkout-top-container"
            style={{ fontSize: '16px', fontWeight: 'bold' }}
          >
            {state.status}
          </div>

          {/* Location, Operator and Tariff info row */}
          <div className="checkout-detail-wrapper">
            <div className="checkout-detail-icon">
              <i className="ri-map-pin-line"></i>
            </div>
            <div>
              <b>Location:</b> {state.address}, {state.postalCode} {state.city},{' '}
              {state.state} {state.country}
            </div>
          </div>
          <div className="checkout-detail-wrapper">
            <div className="checkout-detail-icon">
              <i className="ri-charging-pile-line"></i>
            </div>
            <div>
              <b>{intl.formatMessage({ id: 'checkout.operator' })}:</b>{' '}
              {state.operator}
            </div>
          </div>
          <div className="checkout-detail-wrapper">
            <div className="checkout-detail-icon">
              <i className="ri-price-tag-3-line"></i>
            </div>
            <div>
              <b>{intl.formatMessage({ id: 'checkout.tariffinfo' })}:</b>
            </div>
          </div>

          {state.tariff_data?.price_kwh > 0 && (
            <div className="checkout-detail-wrapper">
              <div className="checkout-detail-icon"></div>
              <div className="checkout-pricing-line-wrapper">
                <div>{intl.formatMessage({ id: 'checkout.pricekwh' })}</div>
                <div>
                  {get_price(state.tariff_data?.price_kwh)}{' '}
                  {currencies[state.tariff_data?.currency]} (
                  {intl.formatMessage({ id: 'checkout.inclvat' })})
                </div>
              </div>
            </div>
          )}
          {state.tariff_data?.price_min > 0 && (
            <div className="checkout-detail-wrapper">
              <div className="checkout-detail-icon"></div>
              <div className="checkout-pricing-line-wrapper">
                <div>{intl.formatMessage({ id: 'checkout.pricemin' })}</div>
                <div>
                  {get_price(state.tariff_data?.price_min)}{' '}
                  {currencies[state.tariff_data?.currency]} (
                  {intl.formatMessage({ id: 'checkout.inclvat' })})
                </div>
              </div>
            </div>
          )}
          {state.tariff_data?.price_session > 0 && (
            <div className="checkout-detail-wrapper">
              <div className="checkout-detail-icon"></div>
              <div className="checkout-pricing-line-wrapper">
                <div>{intl.formatMessage({ id: 'checkout.pricesession' })}</div>
                <div>
                  {get_price(state.tariff_data?.price_session)}{' '}
                  {currencies[state.tariff_data?.currency]} (
                  {intl.formatMessage({ id: 'checkout.inclvat' })})
                </div>
              </div>
            </div>
          )}

          <div
            className="checkout-detail-wrapper"
            style={{ marginTop: '20px' }}
          >
            <div className="checkout-detail-icon"></div>
            <div className="checkout-pricing-line-wrapper">
              <div style={{ fontSize: '10px' }}>
                {intl.formatMessage(
                  { id: 'checkout.authinfo' },
                  {
                    authorzation_amount: (
                      <b>
                        {state.tariff_data?.authorization_amount}{' '}
                        {currencies[state.tariff_data?.currency]}
                      </b>
                    ),
                  },
                )}
              </div>
            </div>
          </div>

          <div
            className="div-with-margin width-100"
            style={{ padding: '0 30px 0 30px' }}
          >
            <PaymentOptions />
          </div>
        </Skeleton>
      </div>

      {/* Card with Checkout Button */}
      <Card className="checkout-card">
        <Skeleton active loading={state.initializing}>
          <div style={{ display: 'flex' }}>
            <i
              className="ri-information-line"
              style={{ width: '40px', paddingLeft: '15px', color: '#1677ff' }}
            ></i>
            <div style={{ width: '96%', paddingRight: '15px' }}>
              {intl.formatMessage({ id: 'checkout.connect.vehicle' })}
            </div>
          </div>

          <img
            src={PaymentCardImg}
            style={{ width: '85vw', maxWidth: '380px', marginTop: '10px' }}
          />

          <Button
            style={{ marginTop: '-20px' }}
            color="primary"
            onClick={onCheckout}
            loading={state.loading}
          >
            <i className="ri-flashlight-line"></i>{' '}
            {intl.formatMessage({ id: 'checkout.button.checkout' })}
          </Button>

          {state.errMsg && <div style={{ color: 'red' }}>{state.errMsg}</div>}

          <Checkbox
            style={{ marginTop: '10px' }}
            value={state.taChecked}
            onChange={(val) => {
              setState({ ...state, taChecked: val, errMsg: null });
            }}
          >
            <div style={{ fontSize: '13px' }}>
              {intl.formatMessage({ id: 'checkout.accept.terms.prefix' })}&nbsp;
              <a
                href="#"
                onClick={() => {
                  setState({ ...state, modalVisible: true });
                }}
              >
                {intl.formatMessage({ id: 'checkout.accept.terms.linktext' })}
              </a>
              .
            </div>
          </Checkbox>
        </Skeleton>
      </Card>

      <Modal
        visible={state.modalVisible}
        footer={null}
        onCancel={() => setState({ ...state, modalVisible: false })}
      >
        <div
          dangerouslySetInnerHTML={{ __html: state.payment_terms_conditions }}
        ></div>
      </Modal>
    </div>
  );
}
