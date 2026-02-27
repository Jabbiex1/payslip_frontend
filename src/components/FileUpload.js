import React from 'react';

export default function FileUpload({ label, name, onChange, required }) {
    return (
        <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>{label}</label>
            <input type="file" name={name} onChange={onChange} required={required} />
        </div>
    );
}
