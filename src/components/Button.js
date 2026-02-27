import React from 'react';

export default function Button({ text, type = 'button' }) {
    return (
        <button
            type={type}
            style={{
                padding: '12px 24px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '16px',
            }}
        >
            {text}
        </button>
    );
}
