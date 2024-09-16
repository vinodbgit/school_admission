 // Basic information

function validateAcademicYear() {
    const field = document.getElementById('academic_year');
    const errorElement = document.getElementById('academic_year_error');
    const value = field.value;
    
    let errorMessage = '';
    if (!value) {
        errorMessage = 'Academic Year is required.';
    } else if (!/^\d{4}-\d{4}$/.test(value)) {
        errorMessage = 'Invalid Academic Year format. Use YYYY-YYYY.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateFirstName() {
    const field = document.getElementById('first_name');
    const errorElement = document.getElementById('first_name_error');
    const value = field.value;
    
    let errorMessage = '';
    if (!value) {
        errorMessage = 'First Name is required.';
    } else if (!/^[A-Za-z]+$/.test(value)) {
        errorMessage = 'First Name must contain only letters.';
    } else if (value.length < 2) {
        errorMessage = 'First name must be at least 2 characters long.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateMiddleName() {
    const field = document.getElementById('middle_name');
    const errorElement = document.getElementById('middle_name_error');
    const value = field.value;
    
    let errorMessage = '';
    if (!value) {
        errorMessage = 'Middle Name is required.';
    } else if (!/^[A-Za-z]+$/.test(value)) {
        errorMessage = 'Middle Name must contain only letters.';
    } else if (value.length < 2) {
        errorMessage = 'Middla name must be at least 2 characters long.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateLastName() {
    const field = document.getElementById('last_name');
    const errorElement = document.getElementById('last_name_error');
    const value = field.value;
    
    let errorMessage = '';
    if (!value) {
        errorMessage = 'Last Name is required.';
    } else if (!/^[A-Za-z]+$/.test(value)) {
        errorMessage = 'Last Name must contain only letters.';
    } else if (value.length < 2) {
        errorMessage = 'Last name must be at least 2 characters long.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateEmail() {
    const field = document.getElementById('parent_email');
    const errorElement = document.getElementById('parent_email_error');
    const value = field.value;
    
    let errorMessage = '';
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!value) {
        errorMessage = 'Email is required.';
    } else if (!emailPattern.test(value)) {
        errorMessage = 'Invalid email format.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validatePhoneNumber() {
    const field = document.getElementById('parent_phone_no');
    const errorElement = document.getElementById('parent_phone_no_error');
    const value = field.value;
    
    let errorMessage = '';
    const phonePattern = /^\d{10}$/;
    if (!value) {
        errorMessage = 'Phone Number is required.';
    } else if (!phonePattern.test(value)) {
        errorMessage = 'Phone Number must be exactly 10 digits.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateGender() {
    const genderRadios = document.getElementsByName('gender');
    const errorElement = document.getElementById('gender_error');
    let errorMessage = '';
    
    let selectedGender = false;
    for (const radio of genderRadios) {
        if (radio.checked) {
            selectedGender = true;
            break;
        }
    }
    
    if (!selectedGender) {
        errorMessage = 'Please select a gender.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

document.querySelectorAll('input[name="gender"]').forEach(radio => {
    radio.addEventListener('change', validateGender);
});

function validateDOB() {
    const field = document.getElementById('dob');
    const errorElement = document.getElementById('dob_error');
    const value = field.value;
    
    let errorMessage = '';
    
    
    if (!value) {
        errorMessage = 'Please enter your date of birth.';
    } else{
        const today = new Date();
        const dob = new Date(value);

        if(dob > today){
        errorMessage = 'Date of Birth cannot be in the future.';
        }
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}


function validatePlaceOfBirth() {
    const field = document.getElementById('place_of_birth');
    const errorElement = document.getElementById('place_of_birth_error');
    const value = field.value.trim();
    
    let errorMessage = '';
    
    if (!value) {
        errorMessage = 'Please enter your place of birth.';
    } else if (value.length < 2) {
        errorMessage = 'Place of Birth must be at least 2 characters long.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateCity() {
    const field = document.getElementById('city');
    const errorElement = document.getElementById('city_error');
    const value = field.value.trim();
    
    let errorMessage = '';
    
    if (!value) {
        errorMessage = 'Please enter your city.';
    } else if (value.length < 2) {
        errorMessage = 'City name must be at least 2 characters long.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validatePinCode() {
    const field = document.getElementById('pin_code');
    const errorElement = document.getElementById('pin_code_error');
    const value = field.value.trim();
    
    let errorMessage = '';
    
    // Check if field is empty
    if (!value) {
        errorMessage = 'Please enter your pin code.';
    } else if (!/^\d{6}$/.test(value)) {
        // Validate if pin code is exactly 6 digits
        errorMessage = 'Pin Code must be exactly 6 digits.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateTaluka() {
    const field = document.getElementById('taluka');
    const errorElement = document.getElementById('taluka_error');
    const value = field.value.trim();
    
    let errorMessage = '';
    
    // Check if field is empty
    if (!value) {
        errorMessage = 'Please enter the taluka.';
    } else if (value.length < 2) {
        // Ensure taluka is at least 2 characters long
        errorMessage = 'Taluka must be at least 2 characters long.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateDistrict() {
    const field = document.getElementById('district');
    const errorElement = document.getElementById('district_error');
    const value = field.value.trim();
    
    let errorMessage = '';
    
    // Check if field is empty
    if (!value) {
        errorMessage = 'Please enter the district.';
    } else if (value.length < 2) {
        // Ensure district is at least 2 characters long
        errorMessage = 'District must be at least 2 characters long.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}

function validateState() {
    const field = document.getElementById('state');
    const errorElement = document.getElementById('state_error');
    const value = field.value.trim();
    
    let errorMessage = '';
    
    // Check if field is empty
    if (!value) {
        errorMessage = 'Please enter the state.';
    } else if (value.length < 2) {
        // Ensure state is at least 2 characters long
        errorMessage = 'State must be at least 2 characters long.';
    }
    
    errorElement.textContent = errorMessage;
    return !errorMessage;
}


function disableSubmit(disable) {
    document.getElementById('submitBtn').disabled = disable;
}


document.getElementById('academic_year').addEventListener('input', validateAcademicYear);
document.getElementById('first_name').addEventListener('input', validateFirstName);
document.getElementById('middle_name').addEventListener('input', validateMiddleName);
document.getElementById('last_name').addEventListener('input', validateLastName);
document.getElementById('parent_email').addEventListener('input', validateEmail);
document.getElementById('parent_phone_no').addEventListener('input', validatePhoneNumber);
document.getElementById('gender').addEventListener('input',validateGender)
document.getElementById('dob').addEventListener('input', validateDOB);
document.getElementById('place_of_birth').addEventListener('input', validatePlaceOfBirth);
document.getElementById('city').addEventListener('input', validateCity);
document.getElementById('pin_code').addEventListener('input', validatePinCode);
document.getElementById('taluka').addEventListener('input', validateTaluka);
document.getElementById('district').addEventListener('input', validateDistrict);
document.getElementById('state').addEventListener('input', validateState);




document.getElementById('admissionForm').addEventListener('input', () => {
    const isAcademicYearValid = validateAcademicYear();
    const isFirstNameValid = validateFirstName();
    const isMiddleNameValid = validateMiddleName();
    const isLastNameValid = validateLastName();
    const isEmailValid = validateEmail();
    const isPhoneNumberValid = validatePhoneNumber();
    const isGenderValid = validateGender();
    const isDOBValid = validateDOB();
    const isPlaceOfBirthValid = validatePlaceOfBirth();
    const isCityValid = validateCity();
    const isPinCodeValid = validatePinCode();
    const isTalukaValid = validateTaluka();
    const isDistrictValid = validateDistrict();
    const isStateValid = validateState();


    disableSubmit(!(isAcademicYearValid && isFirstNameValid && isMiddleNameValid && isLastNameValid && isEmailValid && isPhoneNumberValid && isGenderValid && isDOBValid && isPlaceOfBirthValid && isCityValid && isPinCodeValid  && isTalukaValid && isDistrictValid && isStateValid ));
});




// Initial validation to disable the submit button if any field is empty
validateAcademicYear();
validateFirstName();
validateMiddleName();
validateLastName();
validateEmail();
validatePhoneNumber();
validateGender();
validateDOB();
validatePlaceOfBirth();
validateCity();
validatePinCode();
validateTaluka();
validateDistrict();
validateState();
