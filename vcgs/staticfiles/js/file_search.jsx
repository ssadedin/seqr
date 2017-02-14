var FileList = React.createClass({
    
    getInitialState: function() {
        
        var me = this;
        $.ajax({
            url:'files', dataType:'json'
        }).done(function(result) {
            console.log("received " + result['files'].length + " files in response.");
             me.setState({files:result['files']});
        }).error(function(result) {
           console.log("Damn you kasparov: " + result);
        }); 
        
        return {
            files: [ ]
        };
    },    
    render: function() {
       console.log("Rendering: " + this.state.files);
       var i=0;
       return (<ul>
               {this.state.files.map(function(f) {return (<li key={++i}>{f.path}/{f.file_name}</li>)})}
               </ul>);
    }
});


ReactDOM.render(
        <FileList />,
        document.getElementById('filesbody')
);


$(document).ready(function() {

});        