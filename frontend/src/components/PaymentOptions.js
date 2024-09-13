import * as React from 'react';
import {
  SiApplepay,
  SiGooglepay,
  SiVisa,
  SiMastercard,
  SiAmericanexpress,
} from 'react-icons/si';

export default function PaymentOptions({ size }) {
  const iconSize = size ? size : 28;
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        flex: 1,
        justifyContent: 'space-evenly',
        width: '100%',
      }}
    >
      <SiApplepay size={iconSize} />
      <SiGooglepay size={iconSize} />
      <SiVisa size={iconSize} />
      <SiMastercard size={iconSize} />
      <SiAmericanexpress size={iconSize} />
    </div>
  );
}
