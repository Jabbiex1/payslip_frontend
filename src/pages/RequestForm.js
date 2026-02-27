import React, { useState } from 'react';
import Input from '../components/Input';
import Dropdown from '../components/Dropdown';
import FileUpload from '../components/FileUpload';
import Button from '../components/Button';
import { submitPayslipRequest } from '../api';

export default function RequestForm() {
    const [formData, setFormData] = useState({
        full_name: '',
        employee_number: '',
        department: '',
        job_title: '',
        phone_number: '',
        email: '',
        month: '',
        year: '',
        id_card_front: null,
        id_card_back: null,
    });

    const handleChange = (e) => {
        const { name, value, files } = e.target;
        if (files) {
            setFormData({ ...formData, [name]: files[0] });
        } else {
            setFormData({ ...formData, [name]: value });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = new FormData();
            for (let key in formData) {
                data.append(key, formData[key]);
            }
            const res = await submitPayslipRequest(data);
            alert(`Request submitted successfully!\nReference Number: ${res.data.reference_number}`);
            setFormData({
                full_name: '',
                employee_number: '',
                department: '',
                job_title: '',
                phone_number: '',
                email: '',
                month: '',
                year: '',
                id_card_front: null,
                id_card_back: null,
            });
        } catch (err) {
            console.error(err);
            alert('Error submitting request. Please try again.');
        }
    };

    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    const years = [2023, 2024, 2025, 2026]; // You can adjust

    return (
        <div style={{ maxWidth: '500px', margin: '40px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
            <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>Payslip Request Form</h2>
            <form onSubmit={handleSubmit}>
                <Input label="Full Name" name="full_name" onChange={handleChange} required />
                <Input label="Employee Number" name="employee_number" onChange={handleChange} required />
                <Input label="Department" name="department" onChange={handleChange} required />
                <Input label="Job Title" name="job_title" onChange={handleChange} required />
                <Input label="Phone Number" name="phone_number" onChange={handleChange} required />
                <Input label="Email" name="email" type="email" onChange={handleChange} />
                <Dropdown label="Month" name="month" options={months} onChange={handleChange} required />
                <Dropdown label="Year" name="year" options={years} onChange={handleChange} required />
                <FileUpload label="Upload ID Card Front" name="id_card_front" onChange={handleChange} required />
                <FileUpload label="Upload ID Card Back" name="id_card_back" onChange={handleChange} required />
                <div style={{ textAlign: 'center', marginTop: '20px' }}>
                    <Button text="Submit Request" type="submit" />
                </div>
            </form>
        </div>
    );
}
