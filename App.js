import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const PEXELS_API_KEY = "ERG0gUi0zpSQEf3EI0nLdhSzP61CmdgMtVqCCd7rlOWcCtbaKPqnBZ8s"; // Replace with your actual Pexels API key

function App() {
    const [destination, setDestination] = useState("");
    const [arrivalLocation, setArrivalLocation] = useState("");
    const [departureLocation, setDepartureLocation] = useState("");
    const [travelSeason, setTravelSeason] = useState("");
    const [activityLevel, setActivityLevel] = useState("");
    const [transportPreference, setTransportPreference] = useState("");
    const [foodPreferences, setFoodPreferences] = useState("");
    
    const [itineraryData, setItineraryData] = useState(null);
    const [storyText, setStoryText] = useState("");
    const [currentPage, setCurrentPage] = useState("form"); // form, loading, result
    const [progress, setProgress] = useState(0);
    const [placeImages, setPlaceImages] = useState({});
    const [activeDayTab, setActiveDayTab] = useState(null);

    useEffect(() => {
        // Add proper null check before accessing nested properties
        if (itineraryData && itineraryData.itinerary && itineraryData.itinerary.schedule) {
            const days = Object.keys(itineraryData.itinerary.schedule);
            if (days.length > 0) {
                setActiveDayTab(days[0]);
            }
        }
    }, [itineraryData]);

    const fetchItinerary = async () => {
        setCurrentPage("loading");
        setProgress(10);
        try {
            // Mystery writing animation
            const mysteryWritingInterval = setInterval(() => {
                setProgress(prev => {
                    if (prev < 85) return prev + 5;
                    clearInterval(mysteryWritingInterval);
                    return prev;
                });
            }, 500);

            const response = await axios.get("http://localhost:8000/itinerary/", {
                params: {
                    destination,
                    arrival_location: arrivalLocation,
                    departure_location: departureLocation,
                    travel_season: travelSeason,
                    activity_level: activityLevel,
                    transport_preference: transportPreference,
                    food_preferences: foodPreferences,
                },
            });
            
            clearInterval(mysteryWritingInterval);
            setProgress(90);
            
            const data = response.data;
            setStoryText(data.story);
            setItineraryData(data);
            
            // Add null check before fetching images
            if (data && data.itinerary && data.itinerary.schedule) {
                // Fetch images
                fetchImagesForPlaces(data.itinerary.schedule);
            }
            
            setProgress(100);
            setTimeout(() => {
                setCurrentPage("result");
            }, 500);
            
        } catch (error) {
            console.error("Error fetching itinerary:", error);
            setCurrentPage("form");
            alert("Failed to generate your mystery journey. Please try again.");
        }
    };

    const fetchImagesForPlaces = async (itinerarySchedule) => {
        let images = {};
        
        for (const day in itinerarySchedule) {
            for (const timeOfDay in itinerarySchedule[day]) {
                const activities = itinerarySchedule[day][timeOfDay];
                for (const activity of activities) {
                    if (activity.name && !images[activity.name]) {
                        // Get enhanced query for more mysterious images
                        const enhancedQueryResponse = await axios.get("http://localhost:8000/mysteryimage/", {
                            params: { query: `${activity.name} ${destination}` }
                        });
                        
                        const enhancedQuery = enhancedQueryResponse.data.enhanced_query;
                        images[activity.name] = await fetchPexelsImage(enhancedQuery);
                    }
                }
            }
        }
        setPlaceImages(images);
    };

    const fetchPexelsImage = async (query) => {
        try {
            const response = await axios.get("https://api.pexels.com/v1/search", {
                headers: { Authorization: PEXELS_API_KEY },
                params: { query, per_page: 1 },
            });
            return response.data.photos.length > 0 ? response.data.photos[0].src.large : "/mystery-placeholder.jpg";
        } catch (error) {
            console.error(`Error fetching image for ${query}:`, error);
            return "/mystery-placeholder.jpg"; 
        }
    };

    const handleFormSubmit = (e) => {
        e.preventDefault();
        
        // Form validation
        if (!destination || !arrivalLocation || !departureLocation || !travelSeason || 
            !activityLevel || !transportPreference || !foodPreferences) {
            alert("Please fill in all fields before generating your mystery journey.");
            return;
        }
        
        fetchItinerary();
    };

    const renderForm = () => (
        <div className="journey-form-container">
            <form onSubmit={handleFormSubmit} className="journey-form">
                <div className="form-group">
                    <label>Where do you wish to uncover secrets?</label>
                    <input 
                        type="text" 
                        placeholder="Destination (e.g., Varanasi, Jaipur)" 
                        value={destination} 
                        onChange={(e) => setDestination(e.target.value)} 
                    />
                </div>
                
                <div className="form-row">
                    <div className="form-group">
                        <label>Your arrival point</label>
                        <input 
                            type="text" 
                            placeholder="Arrival Location" 
                            value={arrivalLocation} 
                            onChange={(e) => setArrivalLocation(e.target.value)} 
                        />
                    </div>
                    <div className="form-group">
                        <label>Your departure point</label>
                        <input 
                            type="text" 
                            placeholder="Departure Location" 
                            value={departureLocation} 
                            onChange={(e) => setDepartureLocation(e.target.value)} 
                        />
                    </div>
                </div>
                
                <div className="form-row">
                    <div className="form-group">
                        <label>Season of discovery</label>
                        <select value={travelSeason} onChange={(e) => setTravelSeason(e.target.value)}>
                            <option value="">Select season</option>
                            <option value="Spring">Spring</option>
                            <option value="Summer">Summer</option>
                            <option value="Autumn">Autumn</option>
                            <option value="Winter">Winter</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Your quest intensity</label>
                        <select value={activityLevel} onChange={(e) => setActivityLevel(e.target.value)}>
                            <option value="">Select level</option>
                            <option value="Light">Light - Casual Discovery</option>
                            <option value="Moderate">Moderate - Balanced Adventure</option>
                            <option value="High">High - Intrepid Explorer</option>
                        </select>
                    </div>
                </div>
                
                <div className="form-row">
                    <div className="form-group">
                        <label>Your mode of travel</label>
                        <select value={transportPreference} onChange={(e) => setTransportPreference(e.target.value)}>
                            <option value="">Select transport</option>
                            <option value="Public Transport">Public Transport</option>
                            <option value="Private Car">Private Car</option>
                            <option value="Walking">Walking & Public Transport</option>
                            <option value="Bicycle">Bicycle & Public Transport</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Culinary preferences</label>
                        <input 
                            type="text" 
                            placeholder="Food Preferences" 
                            value={foodPreferences} 
                            onChange={(e) => setFoodPreferences(e.target.value)} 
                        />
                    </div>
                </div>
                
                <button type="submit" className="submit-button">
                    <span>Begin Your Mystery Journey</span>
                </button>
            </form>
        </div>
    );

    const renderLoading = () => (
        <div className="loading-container">
            <div className="mystery-writing">
                <h3>Creating Your Mystery...</h3>
                <div className="animated-quill">
                    <div className="quill"></div>
                    <div className="ink-trail"></div>
                </div>
                <div className="progress-bar-container">
                    <div className="progress-bar" style={{ width: `${progress}%` }}></div>
                </div>
                <p className="loading-message">
                    {progress < 30 && "Unearthing forgotten tales..."}
                    {progress >= 30 && progress < 60 && "Decoding ancient mysteries..."}
                    {progress >= 60 && progress < 90 && "Crafting your adventure..."}
                    {progress >= 90 && "Preparing to reveal secrets..."}
                </p>
            </div>
        </div>
    );

    const renderStoryAndItinerary = () => {
        // Add null check before rendering
        if (!itineraryData || !itineraryData.itinerary || !itineraryData.itinerary.schedule) {
            return (
                <div className="error-container">
                    <h3>Something went wrong with your mystery journey...</h3>
                    <button onClick={() => setCurrentPage("form")} className="back-button">
                        <span>Try Again</span>
                    </button>
                </div>
            );
        }
        
        const { itinerary } = itineraryData;
        const days = Object.keys(itinerary.schedule);
        
        return (
            <div className="result-container">
                <div className="back-button-container">
                    <button onClick={() => setCurrentPage("form")} className="back-button">
                        <span>Create New Mystery</span>
                    </button>
                </div>
                
                <div className="story-section">
                    <h2>The Mystery of {destination}</h2>
                    <div className="story-scroll">
                        <p className="story-text">{storyText}</p>
                    </div>
                </div>
                
                <div className="itinerary-section">
                    <h2>Your Journey Through History</h2>
                    
                    <div className="day-tabs">
                        {days.map((day) => (
                            <button 
                                key={day}
                                className={`day-tab ${activeDayTab === day ? 'active' : ''}`}
                                onClick={() => setActiveDayTab(day)}
                            >
                                {day}
                            </button>
                        ))}
                    </div>
                    
                    {activeDayTab && (
                        <div className="day-content">
                            {["morning", "afternoon", "evening"].map((timeOfDay) => (
                                itinerary.schedule[activeDayTab][timeOfDay] && 
                                itinerary.schedule[activeDayTab][timeOfDay].length > 0 && (
                                    <div key={timeOfDay} className="time-section">
                                        <h3 className="time-title">
                                            <span className="time-icon">{getTimeIcon(timeOfDay)}</span>
                                            {timeOfDay.charAt(0).toUpperCase() + timeOfDay.slice(1)}
                                        </h3>
                                        
                                        <div className="activities-container">
                                            {itinerary.schedule[activeDayTab][timeOfDay].map((activity, index) => (
                                                <div key={index} className="activity-card">
                                                    <div className="activity-image">
                                                        <img 
                                                            src={placeImages[activity.name] || "/mystery-placeholder.jpg"} 
                                                            alt={activity.name} 
                                                        />
                                                    </div>
                                                    <div className="activity-details">
                                                        <h4 className="activity-name">
                                                            <a 
                                                                href={`https://www.google.com/maps/search/${encodeURIComponent(activity.name + " " + destination)}`} 
                                                                target="_blank" 
                                                                rel="noopener noreferrer"
                                                            >
                                                                {activity.name} <span className="map-icon">📍</span>
                                                            </a>
                                                        </h4>
                                                        {activity.description && (
                                                            <p className="activity-description">{activity.description}</p>
                                                        )}
                                                        
                                                        {/* Historical note if available */}
                                                        {itinerary.historical_notes && itinerary.historical_notes[activity.name] && (
                                                            <div className="historical-note">
                                                                <p><i>{itinerary.historical_notes[activity.name]}</i></p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )
                            ))}
                        </div>
                    )}
                </div>
            </div>
        );
    };

    const getTimeIcon = (timeOfDay) => {
        switch(timeOfDay) {
            case 'morning': return '🌅';
            case 'afternoon': return '☀️';
            case 'evening': return '🌙';
            default: return '';
        }
    };

    return (
        <div className="app-container">
            <header className="app-header">
                <h1 className="app-title">Katha Yatra</h1>
                <h2 className="app-subtitle">Where History Becomes Mystery</h2>
            </header>
            
            {currentPage === "form" && renderForm()}
            {currentPage === "loading" && renderLoading()}
            {currentPage === "result" && renderStoryAndItinerary()}
            
            <footer className="app-footer">
                <p>Uncover the stories behind every journey</p>
            </footer>
        </div>
    );
}

export default App;