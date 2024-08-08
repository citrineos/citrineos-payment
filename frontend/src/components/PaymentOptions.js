import * as React from 'react';
import {
  Applepay,
  Googlepay,
  Visa,
  Mastercard,
  Americanexpress,
} from '@icons-pack/react-simple-icons';

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
      <Applepay size={iconSize} />
      <Googlepay size={iconSize} />
      <Visa size={iconSize} />
      <Mastercard size={iconSize} />
      <Americanexpress size={iconSize} />
    </div>
  );
}
