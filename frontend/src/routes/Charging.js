import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { Button, ProgressBar } from 'antd-mobile';
import moment from 'moment';

import axios from '../util/Api.js';
import getConnectorPowerKw from '../util/ConnectorCalculatePower.js';
import { getLocationData } from '../util/getLocationData.js';

export default function Charging() {
  const [locData, setLocData] = React.useState({});
  const [state, setState] = React.useState({
    status: 'waiting', // (inital: 'waiting' / 'rejected' / 'charging' / 'closed' / 'error' )
    statusMessage: null,
    timestamp: '-',
    pricing: null,
    currency: '-',
    chargingTime: 0,
    transaction_kwh: 0,
    power_active_import: null,
    transaction_soc: null,
    initializing: true,
  });

  const navigate = useNavigate();
  const intl = useIntl();
  const { evseId, sessionId } = useParams();

  const refreshTimer = React.useRef(null);
  const sessionNotFoundRetryCounter = React.useRef(0);

  // Memoize setSessionData to prevent useEffect from being called unnecessarily
  const setSessionData = React.useCallback(() => {
    axios
      .get(`checkouts/${sessionId}`)
      .then(({ data }) => {
        // Check if session given
        if (data.remote_request_status !== 'Accepted') {
          setState((prevState) => ({ ...prevState, status: 'rejected' }));
        } else if (data.id && data.transaction_start_time) {
          const transaction = { ...data };
          const newState = {
            ...state,
            ...transaction,
            status: 'charging',
            timestamp: moment().format('DD-MM-YYYY HH:mm:ss'), // Using now() instead of last_updated from MeterValues
          };

          // Calculate charging time from transaction data
          if (transaction.transaction_start_time) {
            if (transaction.transaction_end_time) {
              newState.status = 'closed';
              const moment_start = moment.utc(
                transaction.transaction_start_time,
              );
              const moment_end = moment.utc(transaction.transaction_end_time);
              const diff = moment_end.diff(moment_start, 'seconds');
              newState.chargingTime = diff;
            } else {
              const moment_start = moment.utc(
                transaction.transaction_start_time,
              );
              const moment_now_string = moment().utc().toISOString();
              const moment_now = moment(moment_now_string);
              const diff = moment_now.diff(moment_start, 'seconds');
              newState.chargingTime = diff;
            }
          }
          setState(newState);
          if (!transaction.transaction_end_time) {
            refreshTimer.current = setTimeout(setSessionData, 30 * 1000); // 30s repeat timer, but only if we don't have an end_datetime yet
          }
        } else if (data.id && !data.transaction_start_time) {
          sessionNotFoundRetryCounter.current++;
          if (sessionNotFoundRetryCounter.current <= 3) {
            setTimeout(setSessionData, 5000);
          } else {
            setState((prevState) => ({
              ...prevState,
              status: 'error',
              statusMessage: 'charging.error.sessionnotfound',
            }));
          }
        } else {
          // Do sth when session unknown...
          // navigate('/');
        }
      })
      .catch((e) => {
        // Set error on error
        setState((prevState) => ({
          ...prevState,
          status: 'error',
          statusMessage: e.response?.data?.detail,
        }));
      });
  }, [sessionId, state]);

  React.useEffect(() => {
    if (evseId) {
      // Get EVSE data
      axios.get(`evses/${evseId}`).then(async ({ data }) => {
        // Check if location given
        if (data.id) {
          const location_data = await getLocationData(data);
          setLocationData(location_data);
        } else {
          // Do sth when location unknown...
        }
      });

      // Query session data in parallel
      setSessionData();
    } else {
      // Navigate to home if no location data is given
      navigate('/');
    }

    // Cleanup function to clear the timer on component unmount or re-render
    return () => {
      clearTimeout(refreshTimer.current);
    };
  }, [evseId, navigate, setSessionData]); // Ensure setSessionData is stable by using useCallback

  const setLocationData = (location) => {
    setLocData(location);
  };

  const onRefresh = () => {
    // On manual refresh clear timer and trigger session update which creates new timer
    clearTimeout(refreshTimer.current);
    setSessionData();
  };

  const getFormattedChargingTime = (seconds) => {
    let secs = seconds;
    const hours = secs / 3600;
    secs = secs % 3600;
    const mins = secs / 60;
    secs = secs % 60;
    return `${parseInt(hours, 10)}:${parseInt(mins, 10) < 10 ? `0${parseInt(mins, 10)}` : parseInt(mins, 10)}:${secs < 10 ? `0${parseInt(secs, 10)}` : parseInt(secs, 10)}`;
  };

  return (
    <div className="page-container" style={{ height: '100%', padding: '15px' }}>
      {/* Top row */}
      <div className="checkout-top-container">
        <div>{evseId}</div>
        <div>|</div>
        <div>{locData.power_type}</div>
        <div>|</div>
        <div>
          max.{' '}
          {getConnectorPowerKw(
            locData.max_voltage,
            locData.max_amperage,
            locData.power_type,
          )}{' '}
          kW
        </div>
      </div>

      {/* Charging Speed */}
      <div
        className="width-100 text-align-center"
        style={{ marginTop: '40px', marginBottom: '40px' }}
      >
        <div style={{ fontSize: '24px', fontWeight: '900' }}>
          {/* Icon depending on state */}
          {state.status === 'waiting' ? (
            <i className="ri-lock-unlock-fill"></i>
          ) : state.status === 'charging' ? (
            <i className="ri-flashlight-fill"></i>
          ) : state.status === 'rejected' ? (
            <i className="ri-error-warning-fill"></i>
          ) : state.status === 'closed' ? (
            <i className="ri-check-double-fill"></i>
          ) : (
            <i className="ri-error-warning-fill"></i>
          )}
        </div>

        <div style={{ fontSize: '24px', fontWeight: '900' }}>
          {/* Caption depending on state */}
          {state.status === 'waiting'
            ? intl.formatMessage({ id: 'charging.authorized.waiting' })
            : state.status === 'charging'
              ? `${intl.formatMessage({ id: 'charging.speed' })} ${state.power_active_import !== null ? `: ${state.power_active_import} kW` : ''} `
              : state.status === 'rejected'
                ? intl.formatMessage({ id: 'charging.rejected' })
                : state.status === 'closed'
                  ? intl.formatMessage({ id: 'charging.finished' })
                  : state.statusMessage
                    ? intl.formatMessage({ id: state.statusMessage })
                    : intl.formatMessage({ id: 'global.error.generic' })}
        </div>
        {/* Charging Speed END */}

        {/* Last update timestamp */}
        <div style={{ fontSize: '16px' }}>
          <i className="ri-refresh-fill"></i>{' '}
          {intl.formatMessage({ id: 'charging.lastupdate' })}: {state.timestamp}
        </div>

        {
          /* Refresh button only shown when waiting or charging */
          (state.status === 'charging' || state.status === 'waiting') && (
            <Button onClick={onRefresh} style={{ marginTop: '20px' }}>
              <i className="ri-refresh-line"></i>{' '}
              {intl.formatMessage({ id: 'charging.refresh' })}
            </Button>
          )
        }
      </div>

      {state.status !== 'rejected' ? (
        <>
          {/* Charging Costs */}
          <div className="width-100 div-with-margin charging-info-block">
            <div>
              {intl.formatMessage({ id: 'charging.costs' })} (
              {intl.formatMessage({ id: 'checkout.inclvat' })}):
            </div>
            <div>
              <span>
                {(state.pricing?.total_costs_gross / 100).toFixed(2)}{' '}
              </span>
              <span>{state.pricing?.currency}</span>
            </div>
          </div>

          {/* Charging Time */}
          <div className="width-100 div-with-margin charging-info-block">
            <div>{intl.formatMessage({ id: 'charging.time' })}</div>
            <div>{getFormattedChargingTime(state.chargingTime)}</div>
          </div>

          {/* Energy delivered */}
          <div className="width-100 div-with-margin charging-info-block">
            <div>{intl.formatMessage({ id: 'charging.energy' })}</div>
            <div>{state.transaction_kwh || 0} kWh</div>
          </div>

          {/* SoC */}
          {state.transaction_soc !== null && ( // only shown if we have an SoC
            <>
              <div className="width-100 div-with-margin charging-info-block">
                <div>{intl.formatMessage({ id: 'charging.soc' })}</div>
                <div>{state.transaction_soc} %</div>
              </div>

              {/* SoC ProgressBar */}
              <ProgressBar
                percent={state.transaction_soc}
                style={{
                  width: '100%',
                  '--track-width': '35px',
                  '--fill-color': '#31bd83',
                }}
              />
              <span style={{ fontSize: '16px' }}>
                {intl.formatMessage({ id: 'charging.soc.infotext' })}
              </span>
            </>
          )}
        </>
      ) : (
        /* State is 'rejected' */
        <div className="text-align-center">
          {/* Don't worry */}
          <div
            className="width-100 div-with-margin charging-info-block"
            style={{ justifyContent: 'center' }}
          >
            {intl.formatMessage({ id: 'charging.dontworry' })}
          </div>

          {/* Please try again */}
          <div
            className="width-100 div-with-margin charging-info-block"
            style={{ justifyContent: 'center' }}
          >
            {intl.formatMessage({ id: 'charging.tryagain' })}
          </div>

          <Button
            color="primary"
            onClick={() => navigate(`/checkout/${evseId}`)}
          >
            <i className="ri-flashlight-line"></i>{' '}
            {intl.formatMessage({ id: 'charging.button.again' })}
          </Button>
        </div>
      )}
    </div>
  );
}
