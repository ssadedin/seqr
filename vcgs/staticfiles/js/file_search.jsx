var FileList = React.createClass({
    
    getInitialState: function() {
        
        this._columns = [
             { key: 'file_name', name: 'Name' },
             { key: 'content_type', name: 'Type' },
             { key: 'file_size', name: 'File Size' },
             { key: 'run_id', name: 'Run' },
             { key: 'user_name', name: 'User Name' }
         ]; 
        
        var me = this;
        
        $.ajax({
            url:'files', dataType:'json'
        }).done(function(result) {
            console.log("received " + result['files'].length + " files in response.");
             me.setState({files:result['files']});
        }).error(function(result) {
           console.log("Error receiving file list: " + result);
        }); 
        
        return {
            files: [ ]
        };
    },    
    
    rowGetter: function(i) {
        console.log("Returning file " + i);
        var f = this.state.files[i];
        return {
            file_name : f.file_name,
            content_type : f.content_type,
            file_size : f.file_size,
            run_id : f.run_id,
            user_name : f.user_name
        };
    },
    
    render: function() {
       console.log("Rendering " + this.state.files.length + ' files');

       return  (<ReactDataGrid
                 columns={this._columns}
                 rowGetter={this.rowGetter}
                 rowsCount={this.state.files.length}
                 minHeight={500} />)       ;
    }
});

ReactDOM.render(
        <FileList />,
        document.getElementById('filesbody')
);


$(document).ready(function() {

});        