import React from 'react';

export default function Input({ label, name, type = 'text', onChange, required }) {
    return (
        <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>{label}</label>
            <input
                type={type}
                name={name}
                onChange={onChange}
                required={required}
                style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '6px',
                    border: '1px solid #ccc',
                    fontSize: '14px',
                }}
            />
        </div>
    );
}
