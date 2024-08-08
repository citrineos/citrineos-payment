import axios from '../util/Api.js';

export const getLocationData = async (evse_data) => {
  const connector_data = evse_data.connectors?.[0];
  delete evse_data.connectors;

  const location_data = (await axios.get(`locations/${evse_data.location_id}`))
    .data;
  const operator = location_data.operator?.name;
  delete location_data.operator;
  // const operator_data = (await axios.get(`operators/${location_data.operator_id}`)).data;
  const tariff_data = (await axios.get(`tariffs/${connector_data.tariff_id}`))
    .data;
  delete tariff_data.id;

  return {
    ...evse_data,
    ...connector_data,
    ...location_data,
    operator,
    tariff_data,
  };
};
