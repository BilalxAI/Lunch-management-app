#----------------------------------------------------------------------------------------------------------------------------------------------------------
#Importing Required Libraries
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float , Date ,func,extract,SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from streamlit_option_menu import option_menu
import pandas as pd
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from datetime import date, datetime
import altair as alt

#----------------------------------------------------------------------------------------------------------------------------------------------------
# Set page config
st.set_page_config(
    page_title="Lunch App",
    layout="wide",
    page_icon="food",
    initial_sidebar_state="expanded"
)
# Custom CSS for styling

st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
    }
    body {
            background-color: #f0f0f0;  /* Light grey background */
        }
    .stTextInput>div>div>input {
        background-color: #f8f9fa;
        padding: 1rem;
        font-size: 16px;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
#------------------------------------------------------------------------------------------------------------------------------------------------------- 
#setting up a connection to a PostgreSQL database 
# Replace these variables with your PostgreSQL credentials
username = 'postgres'
password = 'messi-10'
database = 'orm'
host = 'localhost'
port = '5432'
# Create an engine for PostgreSQL
engine = create_engine(f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}')
#initializes a base class for your ORM models.
Base = declarative_base()
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
#creating clases
# Define the Employee class
class Employee(Base):
    __tablename__ = 'employees'  # The table name in the database
    
    id = Column(SmallInteger, primary_key=True, autoincrement=True)  # Auto-incremented ID
    name = Column(String(20), nullable=False)  # Employee's name
    father_name = Column(String(20), nullable=False)  # Father's name
    company_id = Column(SmallInteger, nullable=False,unique=True)  # Company ID
class LunchItem(Base):
    
    __tablename__ = 'lunch_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(20),  nullable=False)
    company_price = Column(SmallInteger, nullable=False)
    personal_price = Column(SmallInteger, nullable=False)
class OrderedLunch(Base):
    __tablename__ = 'ordered_lunch'
    
    id = Column(Integer, primary_key=True)
    employee_name = Column(String)  #  from employee Table
    lunch_item_name = Column(String)  #  from lunch_item Table
    order_date = Column(Date, default=date.today, nullable=False)
    order_day = Column(String, default=datetime.today().strftime('%A'), nullable=False)
    quantity = Column(SmallInteger, nullable=False)
    company_price = Column(SmallInteger, nullable=False)
    personal_price = Column(SmallInteger, nullable=False)
    bykea_price = Column(SmallInteger, nullable=False)

    # Modified relationships using employee_name and lunch_item_name
    employee = relationship(
        "Employee",
        primaryjoin="foreign(OrderedLunch.employee_name) == Employee.name",
        backref="ordered_lunches"
    )
    lunch_item = relationship(
        "LunchItem",
        primaryjoin="foreign(OrderedLunch.lunch_item_name) == LunchItem.item_name",
        backref="ordered_lunches"
    )
#-------------------------------------------------------------------------------------------------------------------------------------------------------------
# Create the tables in PostgreSQL
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

#----------------------------------------------------------------------------------------------------------------------------------------------------------

# employee block functions
# function for getting all employees
def get_all_employees():
    
    session = Session()
    try:
        employees = session.query(Employee).all()
        return employees
    except SQLAlchemyError as e:
        st.error(f"Error retrieving employees: {e}")
        return []
    finally:
        session.close()
#creating function for showing all the emplyoess we have in our office
def show_all_employees():
    
    session = Session()  # ORM session to query the database
    try:
        # Fetch all employees from the database
        employees = get_all_employees()
        
        if employees:
            # Create a list of dictionaries to display in a tabular format
            employee_data = []
            for emp in employees:
                employee_data.append({
                    "ID": emp.id,
                    "Name": emp.name,
                    "Father's Name": emp.father_name,
                    "Company ID": emp.company_id
                })

            # Display the employee details as a table
            st.write("### All Employees")
            st.write(pd.DataFrame(employee_data))
        else:
            st.warning("No employees found in the database.")
    
    except Exception as e:
        st.error(f"Error fetching employees: {e}")
    finally:
        session.close()
#creating function to add new employee if there is a new hiring
def add_employee(name, father_name, company_id):
    #add a new employee to the database 
    session = Session()
    try:
        # Create a new Employee object
        new_employee = Employee(name=name, father_name=father_name, company_id=company_id)
        
        # Add the new employee to the session and commit to the database
        session.add(new_employee)
        session.commit()
        st.success(f"Employee '{name}' added successfully!")
        return True
    except IntegrityError as e:
        session.rollback()
        st.error(f"Error adding employee: {e}")
        return False
    finally:
        session.close()
# this function is for displaying form for adding new emplyoee data , verifying it and adding it
def show_add_employee_form():
    st.markdown("### Add New Employee")
    
    # Employee form
    with st.form("add_employee_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            employee_name = st.text_input("Employee Name", placeholder="Enter employee name")
        with col2:
            father_name = st.text_input("Father's Name", placeholder="Enter father's name")
        with col3:
            company_id = st.text_input("Company ID", placeholder="Enter company ID")

        submit_button = st.form_submit_button("Submit")
        
        if submit_button:
            # Check if all fields are filled
            if employee_name and father_name and company_id:
                # Check if employee already exists (combine employee_name and father_name for uniqueness)
                if check_existing_employee(employee_name, father_name):
                    st.warning(f"Employee with name '{employee_name}' and father's name '{father_name}' already exists.")
                
                else:
                    # Add employee if not already present
                    if add_employee(employee_name, father_name, company_id):
                        
                        st.balloons()
            else:
                st.warning("Please fill all fields")
# creating function to check if the new emplyoee's name and father name already exists or not
def check_existing_employee(employee_name, father_name):
    
    session = Session()  # session to query the database
    try:
        # Query the Employee table to check for existing employee by name and father_name 
        existing_employee = session.query(Employee).filter(
            func.lower(Employee.name) == func.lower(employee_name),
            func.lower(Employee.father_name) == func.lower(father_name)
        ).first()
        
        if existing_employee:
            return True  # Return True if employee exists
        return False  # Return False if no matching employee found
    except Exception as e:
        st.error(f"Error checking employee existence: {e}")
        return False
    finally:
        session.close()
# creating function to delete an emplyoee
def delete_employee(name, father_name):
    #Delete an employee from the database using ORM."""
    session = Session()  # ORM session to interact with the database
    try:
        # Find employee by name, father's name, and company ID
        employee_to_delete = session.query(Employee).filter_by(name=name, father_name=father_name).first()
        
        if employee_to_delete:
            # Delete the employee
            session.delete(employee_to_delete)
            session.commit()
            return True  # Employee deleted successfully
        else:
            st.error(f"Employee '{name}' not found.")
            return False  # Employee not found

    except Exception as e:
        st.error(f"Error deleting employee: {e}")
        return False
    finally:
        session.close()
#showing form for deleting the employe
def show_delete_employee_form():
    st.markdown("### Delete Employee")

    # Display the list of all employees for selection
    session = Session()  #session to query the database
    try:
        # Query to get all employee names
        employees = get_all_employees()
        if employees:
            employee_names = [f"{emp.name} - {emp.father_name} (ID: {emp.company_id})" for emp in employees]
            selected_employee = st.selectbox("Select an employee to delete", employee_names)

            if selected_employee:
                # Extract employee name and company ID from selected string
                selected_name, selected_father_name_and_id = selected_employee.split(' - ')
                selected_father_name, selected_id = selected_father_name_and_id.split(' (ID: ')

                # Remove the closing parenthesis from ID
                selected_id = selected_id.rstrip(')')
                
                # Confirm deletion
                if st.button(f"Delete Employee '{selected_name}'"):
                    # Delete employee from database
                    if delete_employee(selected_name, selected_father_name):
                        st.success(f"Employee '{selected_name}' deleted successfully!")
                        st.balloons()
                    else:
                        st.error("There was an error deleting the employee.")
        else:
            st.warning("No employees found in the database.")
    
    except Exception as e:
        st.error(f"Error fetching employees: {e}")
    finally:
        session.close()
# creating function to update emplyoee's inforamtion
def show_update_employee_form():
    st.markdown("### Update Employee")

    # Display the list of all employees for selection
    session = Session()  # ORM session to query the database
    try:
        # Query to get all employee names
        employees = get_all_employees()
        if employees:
            employee_names = [f"{emp.name} - {emp.father_name} (ID: {emp.company_id})" for emp in employees]
            selected_employee = st.selectbox("Select an employee to update", employee_names)

            if selected_employee:
                # Extract employee name and company ID from selected string
                selected_name, selected_father_name_and_id = selected_employee.split(' - ')
                selected_father_name, selected_id = selected_father_name_and_id.split(' (ID: ')

                # Remove the closing parenthesis from ID
                selected_id = selected_id.rstrip(')')

                # Show the selected employee's current details in text inputs for editing
                with st.form("update_employee_form", clear_on_submit=True):
                    updated_name = st.text_input("new Employee Name")
                    updated_father_name = st.text_input("new Father's Name")
                    updated_company_id = st.text_input("new Company ID")

                    submit_button = st.form_submit_button("Submit Changes")

                    if submit_button:
                        if updated_name and updated_father_name and updated_company_id:
                            if update_employee(selected_name, selected_father_name, selected_id, updated_name, updated_father_name, updated_company_id):
                                st.balloons()
                        else:
                            st.warning("Please fill all fields")
        else:
            st.warning("No employees found in the database.")

    except Exception as e:
        st.error(f"Error fetching employees: {e}")
    finally:
        session.close()
#showing form for updating the employee's inforamtion
def update_employee(current_name, current_father_name, current_company_id, new_name, new_father_name, new_company_id):
    
    session = Session()  # ORM session to interact with the database
    try:
        # Find employee by name, father's name, and company ID
        employee_to_update = session.query(Employee).filter_by(
            name=current_name, father_name=current_father_name, company_id=current_company_id).first()

        if employee_to_update:
            # Update employee details
            employee_to_update.name = new_name
            employee_to_update.father_name = new_father_name
            employee_to_update.company_id = new_company_id
            session.commit()
            st.success(f"Employee '{new_name}' updated successfully!")
            return True  # Employee updated successfully
        else:
            st.error(f"Employee '{current_name}' with company ID '{current_company_id}' not found.")
            return False  # Employee not found

    except Exception as e:
        st.error(f"Error updating employee: {e}")
        return False
    finally:
        session.close()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

# Lunch item block functions
def get_all_lunch_items():
    
    
    session = Session()
    try:
        # Query to fetch all lunch items
        lunch_items = session.query(LunchItem).all()
        return lunch_items
    except Exception as e:
        st.error(f"Error fetching lunch items: {e}")
        return []
    finally:
        session.close()
# creating function for all the items we have in menu to order
def show_all_lunch_items():
    """Display all lunch items."""
    lunch_items = get_all_lunch_items()
    
    if lunch_items:
        # Create a dataframe to display in a table format
        data = []
        for item in lunch_items:
            data.append({
                "Item Name": item.item_name,
                "Company Price": item.company_price,
                "Personal Price": item.personal_price
            })
        
        # Convert data to a pandas DataFrame for better table display
        df = pd.DataFrame(data)
        st.write("### All Lunch Items", df)
    else:
        st.warning("No lunch items available.")
# function for adding new lucnh item along with prices
def add_lunch_item(item_name, company_price, personal_price):
    # Create a session
    session = Session()
    
    try:
        # Create a new LunchItem object
        new_lunch_item = LunchItem(item_name=item_name, company_price=company_price, personal_price=personal_price)
        
        # Add the new lunch item to the session
        session.add(new_lunch_item)
        
        # Commit the transaction to save to the database
        session.commit()
        
        print(f"Lunch item '{item_name}' added successfully!")
        return True
    except IntegrityError:
        # Handle case where duplicate name or other integrity issue occurs
        session.rollback()  # Rollback the session if error occurs
        print(f"Error: Lunch item '{item_name}' already exists or violated constraints.")
        return False
    except Exception as e:
        # Handle any other errors
        session.rollback()
        print(f"Error occurred: {e}")
        return False
    finally:
        # Close the session
        session.close()
# showing form for adding new lunch items
def show_add_lunch_item_form():
    st.markdown("### Add New Lunch Item")

    with st.form("add_lunch_item_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            item_name = st.text_input("Item Name", placeholder="Enter lunch item name")
        
        with col2:
            company_price = st.number_input("Company Price", min_value=0.0, format="%.2f", placeholder="Enter company price")
            personal_price = st.number_input("Personal Price", min_value=0.0, format="%.2f", placeholder="Enter personal price")
        
        submit_button = st.form_submit_button("Submit")

        if submit_button:
            if item_name and (company_price > 0 or personal_price > 0):
                # Call the function to add the lunch item
                if add_lunch_item(item_name, company_price, personal_price):
                    st.success(f"Lunch item '{item_name}' added successfully!")
                    st.balloons()  # Display balloons on success
            else:
                st.warning("Please fill the item name and ensure that at least one of the prices is non-zero.")
# creating function for deleting an lunch item
def delete_lunch_item(item_name):

    """Delete a lunch item from the database based on its name."""
    
    session = Session()
    try:
        # Check if the lunch item exists
        lunch_item = session.query(LunchItem).filter(LunchItem.item_name == item_name).first()
        if lunch_item:
            # Delete the item if it exists
            session.delete(lunch_item)
            session.commit()
            st.success(f"Lunch item '{item_name}' has been deleted successfully.")
        else:
            st.warning(f"Lunch item '{item_name}' not found.")
    except Exception as e:
        st.error(f"Error deleting lunch item: {e}")
    finally:
        session.close()
# showing form for deleting lunch item
def show_delete_lunch_item_form():
    st.markdown("### Delete Lunch Item")
    lunch_items = get_all_lunch_items()  # Fetch all lunch items to populate the select box
    
    # Check if there are lunch items to delete
    if lunch_items:
        item_names = [item.item_name for item in lunch_items]
        selected_item = st.selectbox("Select a lunch item to delete", options=item_names)
        delete_button = st.button("Delete Lunch Item")
        
        if delete_button:
            delete_lunch_item(selected_item)  # Call the delete function with the selected item
    else:
        st.warning("No lunch items available to delete.")
# function for updateing lunch items
def update_lunch_item(item_id, new_item_name, new_company_price, new_personal_price):
    session = Session()
    try:
        # Fetch the item to update
        lunch_item = session.query(LunchItem).filter(LunchItem.item_name == item_id).first()
        if lunch_item:
            # Update details
            lunch_item.item_name = new_item_name
            lunch_item.company_price = new_company_price
            lunch_item.personal_price = new_personal_price
            session.commit()
            st.success(f"Lunch item '{new_item_name}' updated successfully.")
        else:
            st.warning("Lunch item not found.")
    except Exception as e:
        st.error(f"Error updating lunch item: {e}")
    finally:
        session.close()
# function for  showing  form updating lunch items
def show_update_lunch_item_form():
    st.markdown("### Update Lunch Item")
    lunch_items = get_all_lunch_items()  # Fetch all lunch items to populate the select box
    
    # Check if there are any items to update
    if lunch_items:
        # Display selection dropdown with item names and get selected item details
        item_names = [item.item_name for item in lunch_items]
        selected_item = st.selectbox("Select a lunch item to delete", options=item_names)
        
        # Fetch the selected item’s current details
        
        if selected_item:
            with st.form("update_lunch_item_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_item_name = st.text_input("Item's New Name", )
                with col2:
                    new_company_price = st.number_input("NEW Company Price", min_value=0.0)
                with col3:
                    new_personal_price = st.number_input("New Personal Price", min_value=0.0)
                
                submit_button = st.form_submit_button("Update Lunch Item")
                
                if submit_button:
                    # Check the condition: At least one price should be non-zero
                    if new_company_price == 0 and new_personal_price == 0:
                        st.warning("Both prices cannot be zero. Please set at least one price.")
                    else:
                        # Update the item in the database
                        update_lunch_item(selected_item, new_item_name, new_company_price, new_personal_price)
    else:
        st.warning("No lunch items available to update.")
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

# Orders block Functions
# function for getiing all the orders
def get_all_orders():
    
    
    session = Session()
    try:
        orders = session.query(OrderedLunch).all()
        return orders
    except Exception as e:
        st.error(f"Error fetching orders: {e}")
        return []
    finally:
        session.close()
# creating function for adding the ordered lunch
def add_ordered_lunch(employee_ids, lunch_item_id, date, quantity, company_price, personal_price, bykea_price):
    session = Session()
    try:
        with Session(engine) as session:
            # Iterate over each employee and create a new order for each one
            for employee_id in employee_ids:
                new_order = OrderedLunch(
                    employee_id=employee_id,
                    lunch_item_id=lunch_item_id,
                    date=date,
                    quantity=quantity,
                    company_price=company_price*quantity,
                    personal_price=personal_price*quantity,
                    bykea_price=bykea_price
                )
                session.add(new_order)
            session.commit()
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False
def show_add_ordered_lunch_form():
    session = Session()
    st.title(" Add Ordered Lunch")

    # Create columns for form layout
    col1, col2,  = st.columns(2)

    with st.form(key="add_order_form"):
        # Fetch employees and lunch items from the database
        employees = get_all_employees()
        lunch_items = get_all_lunch_items()

        # Select multiple employees
        with col1:
            employee_names = st.multiselect("Select Employees", [employee.name for employee in employees])

        # Select lunch item
        with col2:
            lunch_item_names = st.selectbox("Select Lunch Item", [item.item_name for item in lunch_items])

        # Get lunch item details (company price and personal price)
        selected_lunch_item = session.query(LunchItem).filter(LunchItem.item_name == lunch_item_names).first()
        company_price = selected_lunch_item.company_price
        personal_price = selected_lunch_item.personal_price

        # Quantity input
        with col1:
            quantity = st.number_input("Enter Quantity", min_value=1, value=1)

        # Bykea price (default to 250)
        bykea_price = st.number_input("Bykea Price (default: 250)", min_value=0, value=250)

        # Calendar input for date selection (allowing past dates)
        with col2:
            order_date = st.date_input("Select Order Date")
            order_day = order_date.strftime('%A')  # Get the day of the week from the selected date

        # Display the selected date and day
        st.write(f"Selected Date: {order_date} ({order_day})")

        # Submit button for the form
        submit_button = st.form_submit_button("Add Orders")

        if submit_button:
            if employee_names and lunch_item_names and quantity > 0:
                # List to keep track of employees whose orders are added
                added_employees = []
                
                # For each employee selected, add the order
                for employee_name in employee_names:
                    new_order = OrderedLunch(
                        employee_name=employee_name,
                        lunch_item_name=lunch_item_names,
                        order_date=order_date,
                        order_day=order_day,
                        quantity=quantity,
                        company_price=company_price*1,
                        personal_price=(personal_price*quantity)+(company_price*(quantity-1)),
                        bykea_price=bykea_price
                    )
                    # Add the new entry to the database
                    session.add(new_order)
                    added_employees.append(employee_name)

                # Commit to save the data to the database
                session.commit()
                
                # Display success message with list of employees
                st.success(f"Orders for {', '.join(added_employees)} have been added successfully!")

                # Show the option to add more orders
                st.info("You can now add more orders for other employees.")

                # Reset the form for new input (clearing session state)
                for key in st.session_state.keys():
                    del st.session_state[key]
            else:
                st.warning("Please make sure all fields are filled correctly.")
# function for deleting the oredred lunch
def delete_order(order_id):
    """Delete an order from the database."""
    
    session = Session()
    try:
        order = session.query(OrderedLunch).filter(OrderedLunch.id == order_id).first()
        if order:
            session.delete(order)
            session.commit()
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting order: {e}")
        return False
    finally:
        session.close()
# function for showing form for deleting the orders
def show_delete_order_form():
    """Display the interface for deleting orders."""
    st.markdown("### Delete Lunch Orders")
    
    # Initialize session state for success message if not exists
    if 'delete_success' not in st.session_state:
        st.session_state.delete_success = False
    
    # Show success message if deletion was successful
    if st.session_state.delete_success:
        st.success("Order deleted successfully!")
        st.session_state.delete_success = False  # Reset the flag
    
    # Fetch all orders
    orders = get_all_orders()
    
    if not orders:
        st.warning("No orders found in the database.")
        return

    # Create a list of order descriptions for the select box
    order_options = [
        f"{order.employee_name} - {order.lunch_item_name} - Date: {order.order_date} - Quantity: {order.quantity}"
        for order in orders
    ]

    # Select box for orders
    selected_index = st.selectbox(
        "Select Order to Delete",
        options=range(len(order_options)),
        format_func=lambda x: order_options[x]
    )

    # Show selected order details
    if selected_index is not None:
        selected_order = orders[selected_index]
        
        # Display order details
        st.write("#### Order Details:")
        st.write(f"Employee: {selected_order.employee_name}")
        st.write(f"Lunch Item: {selected_order.lunch_item_name}")
        st.write(f"Date: {selected_order.order_date}")
        st.write(f"Quantity: {selected_order.quantity}")
        st.write(f"Company Price: RS {selected_order.company_price:.2f}")
        st.write(f"Personal Price: RS {selected_order.personal_price:.2f}")

        # Delete button
        if st.button("Delete Order"):
            if delete_order(selected_order.id):
                st.session_state.delete_success = True  # Set success flag
                st.rerun()  # Refresh the page
            else:
                st.error("Failed to delete the order. Please try again.")
#functions for updating the orders
def update_order(order_id, lunch_item_name, quantity, order_date, order_day):
    """Update an existing order in the database."""
    
    session = Session()
    try:
        # Get the order
        order = session.query(OrderedLunch).filter(OrderedLunch.id == order_id).first()
        if not order:
            return False

        # Get the new lunch item to get updated prices
        lunch_item = session.query(LunchItem).filter(LunchItem.item_name == lunch_item_name).first()
        if not lunch_item:
            return False

        # Calculate new total prices based on quantity
        total_company_price = lunch_item.company_price * quantity
        total_personal_price = lunch_item.personal_price * quantity

        # Update the order
        order.lunch_item_name = lunch_item_name
        order.quantity = quantity
        order.order_date = order_date
        order.order_day = order_day
        order.company_price = total_company_price
        order.personal_price = total_personal_price

        session.commit()
        return True
    except Exception as e:
        st.error(f"Error updating order: {e}")
        return False
    finally:
        session.close()
def show_update_order_form():
    
    st.markdown("### Update Lunch Orders")
    
    # Initialize session state for success message if not exists
    if 'update_success' not in st.session_state:
        st.session_state.update_success = False
    
    # Show success message if update was successful
    if st.session_state.update_success:
        st.success("Order updated successfully!")
        st.session_state.update_success = False
    
    # Fetch all orders and lunch items
    orders = get_all_orders()
    lunch_items = get_all_lunch_items()
    
    if not orders:
        st.warning("No orders found in the database.")
        return

    # Create order selection list
    order_options = [
        f"{order.employee_name} - {order.lunch_item_name} - Date: {order.order_date} - Quantity: {order.quantity}"
        for order in orders
    ]

    # Select box for orders
    selected_index = st.selectbox(
        "Select Order to Update",
        options=range(len(order_options)),
        format_func=lambda x: order_options[x]
    )

    if selected_index is not None:
        selected_order = orders[selected_index]
        
        # Create form for updating
        with st.form("update_order_form"):
            st.write("#### Current Order Details:")
            st.write(f"Employee: {selected_order.employee_name}")
            
           
            
            new_lunch_item = st.selectbox(
                "updated Lunch Item",
                options=[item.item_name for item in lunch_items],
                index=0
            )
            
            # Date input
            new_date = st.date_input(
                "updated Date",
                value=selected_order.order_date
            )
            new_day = new_date.strftime("%A")
            
            # Quantity input
            new_quantity = st.number_input(
                "updated Quantity",
                min_value=1
            )
            
            
            
           
            
            # Submit button
            submitted = st.form_submit_button("Update Order")
            
            if submitted:
                if update_order(
                    selected_order.id,
                    new_lunch_item,
                    new_quantity,
                    new_date,
                    new_day
                ):
                    st.session_state.update_success = True
                    st.rerun()
                else:
                    st.error("Failed to update the order. Please try again.")
#------------------------------------------------------------------------------------------------------------------------------------------------------------

# function for getting orders for the selected date
def get_orders_by_date(selected_date):
    
   
    session = Session()
    try:
        orders = session.query(OrderedLunch).filter(OrderedLunch.order_date == selected_date).all()
        return orders
    except Exception as e:
        st.error(f"Error fetching orders: {e}")
        return []
    finally:
        session.close()
# function for showing orders for a selected date
def show_daily_orders():
    session = Session()
    
    st.markdown("### Daily Lunch Orders")


    # Date selection
    selected_date = st.date_input(
        "Select Date",
        value=datetime.today().date()
    )

    # Fetch orders for selected date
    daily_orders = get_orders_by_date(selected_date)

    if not daily_orders:
        st.warning(f"No orders found for {selected_date}")
        return

    # Create DataFrame for display
    orders_data = {
        'Employee': [],
        'Lunch Item': [],
        'Quantity': [],
        'Company Price': [],
        'Personal Price': []
    }

    total_company_price = 0
    total_personal_price = 0
    total_items = 0
    Total_price = 0

    for order in daily_orders:
        orders_data['Employee'].append(order.employee_name)
        orders_data['Lunch Item'].append(order.lunch_item_name)
        orders_data['Quantity'].append(order.quantity)
        orders_data['Company Price'].append(f"{order.company_price:.2f}")
        orders_data['Personal Price'].append(f"{order.personal_price:.2f}")

        # Add to totals
        total_company_price += order.company_price
        total_personal_price += order.personal_price
        total_items += order.quantity

    
    orders_today = session.query(OrderedLunch).filter(OrderedLunch.order_date == selected_date).all()
    if orders_today:
        max_bykea_price = session.query(func.max(OrderedLunch.bykea_price)).filter(OrderedLunch.order_date == selected_date).scalar()

    Total_price = total_company_price + total_personal_price+max_bykea_price
    
   

    
    # Convert to DataFrame
    df = pd.DataFrame(orders_data)

    # Display summary statistics
    st.markdown(f"#### Summary for {selected_date} ({daily_orders[0].order_day})")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.info(f"Total Orders: {len(daily_orders)}")
    with col2:
        st.info(f"Bykea price: {max_bykea_price}")
    with col3:
        st.info(f"Total Company Price: RS {total_company_price:.2f}")
    with col4:
        st.info(f"Total Personal Price: RS {total_personal_price:.2f}")
    with col5:
        st.info(f"Total Price: RS {Total_price:.2f}")
    

    # Display detailed orders table
    st.markdown("#### Detailed Orders")
    st.dataframe(
        df,
        column_config={
            "Employee": st.column_config.TextColumn("Employee"),
            "Lunch Item": st.column_config.TextColumn("Lunch Item"),
            "Quantity": st.column_config.NumberColumn("Quantity"),
            "Company Price": st.column_config.TextColumn("Company Price"),
            "Personal Price": st.column_config.TextColumn("Personal Price")
        },
        hide_index=True,
    )

    # Export functionality
    if st.button("Export Daily Orders"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"lunch_orders_{selected_date}.csv",
            mime="text/csv"
        )

    

#--------------------------------------------------------------------------------------------------------------------------------------------------------------

#monthly orders block

def get_orders_for_month(month, year):
    #Retrieve all orders for the specified month and year 
    session = Session()
    try:
        
        orders = session.query(OrderedLunch).filter(
            extract('month', OrderedLunch.order_date) == month,
            extract('year', OrderedLunch.order_date) == year
        ).order_by(OrderedLunch.order_date).all()
        return orders
    except Exception as e:
        st.error(f"Error fetching orders: {e}")
        return []
    finally:
        session.close()


def calculate_total_bykea_price_for_month(month, year):
    session = Session()

    # Query orders for the selected month and year
    orders = session.query(OrderedLunch).filter(
        extract('month', OrderedLunch.order_date) == month,
        extract('year', OrderedLunch.order_date) == year
    ).order_by(OrderedLunch.order_date).all()

    # Dictionary to store max Bykea price for each unique day
    daily_max_bykea_prices = {}

    for order in orders:
        order_date = order.order_date
        # Update the max Bykea price for the day
        if order_date not in daily_max_bykea_prices:
            daily_max_bykea_prices[order_date] = order.bykea_price
        else:
            daily_max_bykea_prices[order_date] = max(daily_max_bykea_prices[order_date], order.bykea_price)

    # Calculate the total Bykea price for the entire month
    total_bykea_price = sum(daily_max_bykea_prices.values())

    # Create DataFrame for display
    df = pd.DataFrame(list(daily_max_bykea_prices.items()), columns=['Date', 'Max Bykea Price'])

    return total_bykea_price, df

def show_orders_for_month():
    st.markdown("### Monthly Lunch Orders")
    
    # Date selection
    current_month = datetime.today().month
    current_year = datetime.today().year
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox(
            "Select Month", 
            list(range(1, 13)), 
            format_func=lambda x: datetime(2024, x, 1).strftime('%B'),
            index=current_month - 1
        )
    with col2:
        selected_year = st.number_input("Select Year", min_value=2000, max_value=2024, value=current_year)
    
    # Retrieve orders data
    monthly_orders = get_orders_for_month(selected_month, selected_year)
    
    if monthly_orders:
        # Create DataFrame from ORM objects
        orders_data = {
            'Date': [],
            'Employee': [],
            'Lunch Item': [],
            'Quantity': [],
            'Company Price': [],
            'Personal Price': []
        }
        
        for order in monthly_orders:
            orders_data['Date'].append(order.order_date)
            orders_data['Employee'].append(order.employee_name)
            orders_data['Lunch Item'].append(order.lunch_item_name)
            orders_data['Quantity'].append(order.quantity)
            orders_data['Company Price'].append(order.company_price)
            orders_data['Personal Price'].append(order.personal_price)
        
        df = pd.DataFrame(orders_data)
        bykea_total,df1=calculate_total_bykea_price_for_month(selected_month,selected_year)
        
        # Calculate summary statistics
        total_orders = len(df)
        
        total_company_cost = df['Company Price'].sum()
        total_personal_cost = df['Personal Price'].sum()
        tota_price=total_company_cost+total_personal_cost+bykea_total
        # Display summary metrics
        st.markdown(f"#### Summary for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")
        col1, col2, col3,col4 ,col5= st.columns(5)
        with col1:
            st.info(f"Total Orders: {total_orders}")
        
        with col2:
            st.info(f"Company Cost: RS {total_company_cost:.2f}")
        with col3:
            st.info(f"Personal Cost: RS {total_personal_cost:.2f}")
        with col4:
            st.info(f"Total Bykea Cost: RS {bykea_total:.2f}")
        with col5:
            st.info(f"Total Cost: RS {tota_price:.2f}")
        
       
        # Create price comparison chart
        st.markdown("#### Price Comparison by Employee")

        # Group by Employee and sum the prices
        price_comparison = df.groupby('Employee').agg({
            'Company Price': 'sum',
            'Personal Price': 'sum'
        }).reset_index()

        # Reshape data for plotting
        price_data = pd.melt(
        price_comparison, 
        id_vars=['Employee'],
        value_vars=['Company Price', 'Personal Price'],
        var_name='Price Type',
        value_name='Amount'
)

        # Create custom color scale for Company Price (Purple) and Personal Price (Grey)
        color_scale = alt.Scale(
            domain=['Company Price', 'Personal Price'],
            range=['#9c27b0', '#ffffff']  # Purple for Company, Grey for Personal
        )

        # Create bar chart with custom colors
        chart = alt.Chart(price_data).mark_bar().encode(
            x=alt.X('Employee:N', title='Employee'),
            y=alt.Y('Amount:Q', title='Price ($)'),
            color=alt.Color(
                'Price Type:N',
                title='Price Type',
                scale=color_scale
            ),
            tooltip=['Employee', 'Price Type', 'Amount']
        ).properties(
            height=400
        ).configure_axis(
            grid=True,
            gridColor='#e0e0e0'  # Light grey grid lines
        )

        # Display the chart in Streamlit
        st.altair_chart(chart, use_container_width=True)

        
        # Display detailed table
        st.markdown("#### Detailed Orders")
        st.dataframe(
            df,
            column_config={
                "Date": st.column_config.DateColumn("Date"),
                "Employee": st.column_config.TextColumn("Employee"),
                "Lunch Item": st.column_config.TextColumn("Lunch Item"),
                "Quantity": st.column_config.NumberColumn("Quantity"),
                "Company Price": st.column_config.NumberColumn(
                    "Company Price",
                    format="%.2f"
                ),
                "Personal Price": st.column_config.NumberColumn(
                    "Personal Price",
                    format="%.2f"
                )
            },
            hide_index=True
        )


        st.dataframe(df1)
        
        # Export functionality
        if st.button("Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"lunch_orders_{selected_year}_{selected_month}.csv",
                mime="text/csv"
            )
    else:
        st.warning(f"No orders found for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")
#-------------------------------------------------------------------------------------------------------------------------------------------------------------

# FUNCTION FOR CALCULTING AND SHOWING MONTHY ORDERS FOR A EMPLOYEE
def show_monthly_orders_for_employee():
    st.markdown("### Monthly Orders for a Specified Employee")
    
    # Date selection
    current_month = datetime.today().month
    current_year = datetime.today().year
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox(
            "Select Month", 
            list(range(1, 13)), 
            format_func=lambda x: datetime(2024, x, 1).strftime('%B'),
            index=current_month - 1
        )
    with col2:
        selected_year = st.number_input("Select Year", min_value=2000, max_value=2024, value=current_year)
    
    # Fetch all employees
    all_employees = get_all_employees()  # Replace with your ORM query for fetching all employees
    employee_names = [employee.name for employee in all_employees]  # Adjust to match your Employee model field name
    
    # User selects an employee
    selected_employee = st.selectbox("Select Employee", employee_names)
    
    # Retrieve orders for the selected employee in the selected month and year
    monthly_orders = get_orders_for_month(selected_month, selected_year)  # Existing function
    employee_orders = [order for order in monthly_orders if order.employee_name == selected_employee]
    
    if employee_orders:
        # Create DataFrame for the employee's orders
        orders_data = {
            'Date': [],
            'Lunch Item': [],
            'Quantity': [],
            'Company Price': [],
            'Personal Price': []
        }
        
        for order in employee_orders:
            orders_data['Date'].append(order.order_date)
            orders_data['Lunch Item'].append(order.lunch_item_name)
            orders_data['Quantity'].append(order.quantity)
            orders_data['Company Price'].append(order.company_price)
            orders_data['Personal Price'].append(order.personal_price)
        
        df = pd.DataFrame(orders_data)
        
        # Calculate totals
        total_orders = len(df)
        total_company_cost = df['Company Price'].sum()
        total_personal_cost = df['Personal Price'].sum()
        total_cost=total_company_cost+total_personal_cost
        
        # Display summary metrics
        st.markdown(f"#### Summary for {selected_employee} in {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")
        col1, col2, col3,col4 = st.columns(4)
        with col1:
            st.info(f"Total Orders: {total_orders}")
        with col2:
            st.info(f"Company Price: RS {total_company_cost:.2f}")
        with col3:
            st.info(f"Personal Price: RS {total_personal_cost:.2f}")
        with col4:
            st.info(f"Total Cost: RS {total_cost:.2f}")
        
        # Display detailed orders
        st.markdown("#### Detailed Orders")
        st.dataframe(
            df,
            column_config={
                "Date": st.column_config.DateColumn("Date"),
                "Lunch Item": st.column_config.TextColumn("Lunch Item"),
                "Quantity": st.column_config.NumberColumn("Quantity"),
                "Company Price": st.column_config.NumberColumn(
                    "Company Price",
                    format="%.2f"
                ),
                "Personal Price": st.column_config.NumberColumn(
                    "Personal Price",
                    format="%.2f"
                )
            },
            hide_index=True
        )
        
        # Export functionality
        if st.button(f"Export {selected_employee}'s Orders to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{selected_employee}_orders_{selected_year}_{selected_month}.csv",
                mime="text/csv"
            )
    else:
        st.warning(f"No orders found for {selected_employee} in {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")
#-----------------------------------------------------------------------------------------------------------------------------------------------------------

# function for calculting total billing
def calculate_monthly_totals():
    st.markdown("### Monthly Price Totals")
    
    # Date selection
    current_month = datetime.today().month
    current_year = datetime.today().year
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox(
            "Select Month", 
            list(range(1, 13)), 
            format_func=lambda x: datetime(2024, x, 1).strftime('%B'),
            index=current_month - 1
        )
    with col2:
        selected_year = st.number_input("Select Year", min_value=2000, max_value=2024, value=current_year)
    
    # Retrieve orders for the selected month and year
    monthly_orders = get_orders_for_month(selected_month, selected_year)  # Fetch orders from database
    
    if monthly_orders:
        # Create DataFrame for the orders
        orders_data = {
            'Employee': [],
            'Company Price': [],
            'Personal Price': []
        }
        
        for order in monthly_orders:
            orders_data['Employee'].append(order.employee_name)
            orders_data['Company Price'].append(order.company_price)
            orders_data['Personal Price'].append(order.personal_price)
        
        df = pd.DataFrame(orders_data)
        
        # Calculate totals
        total_orders = len(df)
        total_company_cost = df['Company Price'].sum()
        total_personal_cost = df['Personal Price'].sum()
        
        bykea,df1=calculate_total_bykea_price_for_month(selected_month,selected_year)
        total_price = total_company_cost + total_personal_cost+bykea
        # Display summary metrics
        st.markdown(f"#### Total Summary for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")
        col1, col2, col3,col4 = st.columns(4)
        with col1:
            st.info(f"Total Orders: {total_orders}")
        with col2:
            st.info(f"Total Company Cost: RS {total_company_cost:.2f}")
        with col3:
            st.info(f"Total Personal Cost: RS {total_personal_cost:.2f}")
        with col4:
            st.info(f"Total Bykea Cost: RS {bykea:.2f}")
        st.markdown(f"#### Total Combined Price: RS {total_price:.2f}")
        
        
    else:
        st.warning(f"No orders found for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")

#------------------------------------------------------------------------------------------------------------------------------------------------------------
#main function block
def main():
    # Sidebar navigation
    with st.sidebar:
        selected = option_menu(
            menu_title=None,
            options=["Home", "Employees", "Lunch Items", "Ordered Lunch", "Show Daily Orders", "Monthly Orders", "Employee Monthly", 'Monthly Billing'],
            icons=["house", "person", "cup-hot", "cart-plus", "list-ul", "list-ul", "list-ul", 'credit-card']
        )

    # selecting from the navigation which option to select
    if selected == "Home":
        st.markdown(
        """
        <h1 style='font-size: 50px; font-weight: bold; text-align: center;'>
            🍔 Welcome to the Employee Lunch Order Tracker 🍕
        </h1>
        """, unsafe_allow_html=True)
        st.image("/home/bilal/Documents/project/IMG_2999.jpg", width=1000)
        st.markdown("""
            This app helps you manage and track lunch orders for employees. 
            You can:
            - Add Employees
            - Add Lunch Items
            - ADD Lunch orders
            - View Order history
            - Calculate Total bill
        """)

    elif selected == "Employees":
        # Employees section navigation
        employee_action = option_menu(
            menu_title="Employees",  # This section is for employee-related actions
            options=["ALL Employee","Add Employee", "Delete Employee", "Update Employee"],  # Four options for employees
            icons=["person","person-plus", "trash", "pencil"],
            default_index=0,
        )
        
        if  employee_action == "ALL Employee":
            show_all_employees()
        elif employee_action == "Add Employee":
            show_add_employee_form() 
        elif employee_action == "Delete Employee":
            show_delete_employee_form()  # Show form to delete employee
        elif employee_action == "Update Employee":
            show_update_employee_form()
    
    elif selected == "Lunch Items":
        lunch_item_action = option_menu(
        menu_title="Lunch Items",  # This section is for lunch item-related actions
        options=["show all lunch items","Add Lunch Item", "Delete Lunch Item", "Update Lunch Item"],  # Four  options for lunch items
        icons=["cup-hot", "trash", "pencil"],
        default_index=0,
              )
        if lunch_item_action == "show all lunch items":
            show_all_lunch_items()
        elif lunch_item_action == "Add Lunch Item":
             show_add_lunch_item_form() 
            # Show form to add lunch item
        elif lunch_item_action == "Delete Lunch Item":
            show_delete_lunch_item_form()
        elif lunch_item_action == "Update Lunch Item":
            show_update_lunch_item_form()  #

    elif selected == "Ordered Lunch":
        # Employees section navigation
        employee_action = option_menu(
            menu_title="",  # This section is for employee-related actions
            options=["Add order", "Delete Orders", "Update Orders"],  # Three options for employees
            icons=["person","person-plus", "trash", "pencil"],
            default_index=0,
        )
        


       # if  employee_action == "ALL Orders":
        #    show_all_orders()

        if  employee_action == "Add order":
            show_add_ordered_lunch_form()
        elif  employee_action == "Delete Orders":
            show_delete_order_form()
        elif  employee_action == "Update Orders":
            show_update_order_form()
    elif selected == "Show Daily Orders":
        show_daily_orders()
    elif selected == "Monthly Orders":
        show_orders_for_month()
    elif selected == "Employee Monthly":
        show_monthly_orders_for_employee()
    elif selected == "Monthly Billing":
        calculate_monthly_totals()





  #calling main      
#------------------------------------------------------------------------------------------------------------------------------------------------------------

# calling main function
if __name__ == "__main__":
    main()