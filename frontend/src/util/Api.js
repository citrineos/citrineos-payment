import axios from 'axios';
import {message} from "antd";

const CLIENT_API_URL = process.env.NODE_ENV === 'development' 
  ? process.env.REACT_APP_CLIENT_API_URL 
  : window.CLIENT_API_URL;


console.log({CLIENT_API_URL});

const axiosObj = axios.create({
  baseURL: CLIENT_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosObj.interceptors.response.use(function (response) {
  // console.log('Logging successful response', {response});

  // return the final response
  return response;

}, function (err) {
  console.log('Logging error config response', {err});

  if(!err.response) {
    // We have a network error, showing an apropriate message.
    message.error("NETWORK ERROR - Please try again later.");
  } 

  return Promise.reject(err);
});

export default axiosObj;
