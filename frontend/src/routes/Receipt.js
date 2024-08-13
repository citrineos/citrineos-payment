import React from 'react';
import { useParams } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { Skeleton } from 'antd';
import moment from 'moment';

import axios from '../util/Api.js';

const Receipt = () => {
  const [receiptData, setReceiptData] = React.useState(null);
  const [ocmfData, setOcmfData] = React.useState(null);
  const { sessionId } = useParams();
  const intl = useIntl();

  // Get the session data on load
  React.useEffect(() => {
    if (sessionId) {
      axios.get(`receipts/${sessionId}`).then(({ data }) => {
        if (data.data) {
          // Check for transaction_data and try to get OCMF if available
          const transaction_data = data?.data?.session?.transaction_data;
          if (transaction_data) {
            try {
              transaction_data.forEach((transacionData) => {
                transacionData.sampled_value.forEach((sampledValue) => {
                  if (sampledValue.format === 'SignedData') {
                    // searching for signeddata
                    const match = /(4f434d46{1}.*)/g.exec(sampledValue.value);
                    if (match) {
                      // found hex ocmf, decode to plain text
                      const result = [];
                      for (let i = 0; i < sampledValue.value.length; i += 2) {
                        result.push(
                          String.fromCharCode(
                            parseInt(sampledValue.value.substr(i, 2), 16),
                          ),
                        );
                      }
                      const ocmf = result.join('');
                      setOcmfData(ocmf);
                    }
                  }
                });
              });
            } catch (e) {
              const tdata = JSON.stringify(transaction_data);
              const rx =
                /("sampled_value": \[{"value": ")(OCMF\|{1}.*\|{1}.*{"SD":"{1}.*"})(",)/g;
              const match = rx.exec(tdata);
              if (match) {
                setOcmfData(match[2]);
              }
            }
          }
          setReceiptData(data.data);
        } else if (data.message) {
          // Do sth when no session found but message
        }
      });
    }
  }, [sessionId]);

  const downloadOcmfFile = () => {
    const element = document.createElement('a');
    const file = new Blob([ocmfData], {
      type: 'text/plain',
    });
    element.href = URL.createObjectURL(file);
    element.download = `ocmf_${receiptData.id}.txt`;
    document.body.appendChild(element);
    element.click();
  };

  return (
    <div className="receipt-main-container">
      <div className="receipt-inner-container">
        <div className="receipt-header-row">
          <div>AMPAY</div>
          <div className="receipt-header-row-subtitle">SCAN - PAY - CHARGE</div>
        </div>
        <div className="receipt-content-container">
          <Skeleton active loading={false /* !sessionData*/}>
            <div>
              <p>
                <b>{intl.formatMessage({ id: 'receipt.sessiondetails' })}:</b>
              </p>
              <p>
                <span>
                  Session ID: {receiptData?.session?.id}
                  <br />
                  EVSE ID: {receiptData?.connector?.evse_id}
                  <br />
                  {intl.formatMessage({ id: 'checkout.operator' })}:{' '}
                  {receiptData?.operator.fullname}
                  <br />
                  {intl.formatMessage({ id: 'receipt.starttime' })}:{' '}
                  {moment(receiptData?.start_time).format(
                    'YYYY-MM-DD HH:mm:ss',
                  )}
                  <br />
                  {intl.formatMessage({ id: 'receipt.stoptime' })}:{' '}
                  {moment(receiptData?.end_time).format('YYYY-MM-DD HH:mm:ss')}
                  <br />
                  {intl.formatMessage({ id: 'receipt.address' })}:{' '}
                  {`${receiptData?.location?.street} ${receiptData?.location?.street_number}, ${receiptData?.location?.postal_code} ${receiptData?.location?.city}, ${receiptData?.location?.country}`}
                  <br />
                  {intl.formatMessage({ id: 'receipt.meterstart' })}:{' '}
                  {`${(receiptData?.session?.meter_start / 1000)?.toFixed(2)} kWh`}
                  <br />
                  {intl.formatMessage({ id: 'receipt.meterstop' })}:{' '}
                  {`${(receiptData?.session?.meter_stop / 1000)?.toFixed(2)} kWh`}
                  <br />
                  {ocmfData && (
                    <span>
                      Download OCMF (Eichrecht):{' '}
                      <a onClick={downloadOcmfFile}>Download</a>
                    </span>
                  )}
                </span>
              </p>
            </div>
            <div style={{ overflow: 'scroll' }}>
              <p>
                <b>{intl.formatMessage({ id: 'receipt.sessioncosts' })}:</b>
              </p>
              <table>
                <thead>
                  <tr>
                    <td>Position</td>
                    <td>
                      {intl.formatMessage({ id: 'receipt.measuredvalue' })}
                    </td>
                    <td>
                      {intl.formatMessage({ id: 'receipt.unitprice' })}{' '}
                      {` (${receiptData?.session?.final_pricing?.currency})`}
                    </td>
                    <td>
                      {intl.formatMessage({ id: 'receipt.netprice' })}{' '}
                      {` (${receiptData?.session.final_pricing?.currency})`}
                    </td>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Session</td>
                    <td>{1}</td>
                    <td>{receiptData?.pricing?.price_session?.toFixed(2)}</td>
                    <td>
                      {(receiptData?.session?.final_pricing?.session_costs
                        ? receiptData?.session?.final_pricing?.session_costs /
                          100
                        : 0
                      ).toFixed(2)}
                    </td>
                  </tr>
                  <tr>
                    <td>{intl.formatMessage({ id: 'receipt.consumption' })}</td>
                    <td>
                      {
                        receiptData?.session?.final_pricing
                          ?.energy_consumption_kwh
                      }
                    </td>
                    <td>{receiptData?.pricing?.price_kwh?.toFixed(2)}</td>
                    <td>
                      {(receiptData?.session?.final_pricing?.energy_costs
                        ? receiptData?.session?.final_pricing?.energy_costs /
                          100
                        : 0
                      ).toFixed(2)}
                    </td>
                  </tr>
                  <tr>
                    <td>{intl.formatMessage({ id: 'receipt.time' })}</td>
                    <td>
                      {receiptData?.session?.end_time &&
                      receiptData?.session?.start_time
                        ? moment
                            .utc(
                              moment(receiptData.session.end_time).diff(
                                moment(receiptData.session.start_time),
                                'seconds',
                              ) * 1000,
                            )
                            .format('HH:mm:ss')
                        : '00:00:00'}
                    </td>
                    <td>{receiptData?.pricing?.price_min?.toFixed(2)}</td>
                    <td>
                      {(receiptData?.session?.final_pricing?.time_costs
                        ? receiptData?.session?.final_pricing?.time_costs / 100
                        : 0
                      ).toFixed(2)}
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan="3">
                      {intl.formatMessage({ id: 'receipt.totalnet' })}
                    </td>
                    <td>
                      {(
                        receiptData?.session?.final_pricing?.total_costs_net /
                        100
                      )?.toFixed(2)}
                    </td>
                  </tr>
                  <tr>
                    <td colSpan="3">
                      {intl.formatMessage({ id: 'receipt.vat' })} (
                      {receiptData?.session?.final_pricing?.tax_rate}%)
                    </td>
                    <td>
                      {
                        // Gross minus Net
                        (
                          receiptData?.session?.final_pricing
                            ?.total_costs_gross /
                            100 -
                          receiptData?.session?.final_pricing?.total_costs_net /
                            100
                        ).toFixed(2)
                      }
                    </td>
                  </tr>
                  <tr>
                    <td colSpan="3">
                      {intl.formatMessage({ id: 'receipt.totalgross' })}
                    </td>
                    <td>
                      {(
                        receiptData?.session?.final_pricing?.total_costs_gross /
                        100
                      )?.toFixed(2)}
                    </td>
                  </tr>
                  {receiptData?.session?.final_pricing?.from_auth && (
                    <>
                      <tr>
                        <td colSpan="3">
                          {intl.formatMessage({ id: 'receipt.discount' })}
                        </td>
                        <td>
                          {(
                            (receiptData?.session?.final_pricing
                              ?.total_costs_gross -
                              receiptData?.session?.final_pricing?.from_auth
                                ?.total_costs_gross) /
                            100
                          )?.toFixed(2)}
                        </td>
                      </tr>
                      <tr>
                        <td colSpan="3">
                          {intl.formatMessage({ id: 'receipt.finalpricing' })}
                        </td>
                        <td>
                          {(
                            receiptData?.session?.final_pricing?.from_auth
                              ?.total_costs_gross / 100
                          )?.toFixed(2)}
                        </td>
                      </tr>
                    </>
                  )}
                </tfoot>
              </table>
            </div>
            <div style={{ marginTop: '40px' }}>
              <p>{intl.formatMessage({ id: 'receipt.enjoyedcharging' })}</p>
              <p>
                {intl.formatMessage({ id: 'receipt.problemsoperator' })}:{' '}
                {receiptData?.operator?.fullname}{' '}
              </p>
            </div>
          </Skeleton>
        </div>
        <div className="receipt-footer-row">
          <div>
            {intl.formatMessage({ id: 'receipt.footermsg' })}{' '}
            {receiptData?.operator?.fullname} (
            {intl.formatMessage({ id: 'checkout.operator' })})
          </div>
        </div>
      </div>
    </div>
  );
};

export default Receipt;
